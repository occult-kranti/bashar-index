(() => {
  // native-observer.js
  function createAcceptedSabrObserver({ scope = window, sdk, videoId, timeoutMs = 45e3 }) {
    const need2 = (ok, code) => {
      if (!ok) throw Error(code);
    };
    need2(/^[A-Za-z0-9_-]{11}$/.test(videoId), "invalid_video_id");
    need2(sdk?.VideoPlaybackAbrRequest?.decode && sdk?.FormatXTags?.decode && sdk?.buildSabrFormat, "observer_sdk_missing");
    const originalFetch = scope.fetch, proto = scope.XMLHttpRequest?.prototype, originalOpen = proto?.open, originalSend = proto?.send;
    const xhrs = /* @__PURE__ */ new WeakMap();
    let finished = false, secret = null, timer, watcher, resolveReady, rejectReady, inspecting = false, observations = 0, lastReason = null, activeReader = null;
    const ready = new Promise((resolve, reject) => {
      resolveReady = resolve;
      rejectReady = reject;
    });
    ready.catch(() => {
    });
    const bytes = (value) => {
      if (value instanceof Uint8Array) return value;
      if (value instanceof ArrayBuffer) return new Uint8Array(value);
      if (ArrayBuffer.isView(value)) return new Uint8Array(value.buffer, value.byteOffset, value.byteLength);
      return null;
    };
    const base64 = (value) => Uint8Array.from(atob(decodeURIComponent(value).replace(/-/g, "+").replace(/_/g, "/")), (x) => x.charCodeAt(0));
    const equal = (a, b) => a.length === b.length && a.every((x, i) => x === b[i]);
    const formatKey = (f) => JSON.stringify([f.itag, String(f.lastModified), f.xtags || ""]);
    function context() {
      const url = new URL(scope.location.href), player = scope.document.getElementById("movie_player"), video = player?.querySelector("video");
      need2(url.origin === "https://www.youtube.com" && url.pathname === "/watch" && url.searchParams.get("v") === videoId && player?.getVideoData?.().video_id === videoId, "source_changed");
      need2(video && !video.mediaKeys && !video.error && !player.classList.contains("ad-showing") && !player.classList.contains("ad-interrupting"), "source_not_eligible");
      need2(Number.isFinite(video.duration) && video.duration > 0, "source_duration_unknown");
      const response = player.getPlayerResponse?.() || scope.ytInitialPlayerResponse;
      need2(response?.videoDetails?.videoId === videoId && response.playabilityStatus?.status === "OK", "response_identity_changed");
      need2(response.videoDetails.isLive !== true && !response.videoDetails.isPostLiveDvr, "live_source_unsupported");
      return { player, video, response };
    }
    function restore() {
      clearTimeout(timer);
      clearInterval(watcher);
      if (scope.fetch === wrappedFetch) scope.fetch = originalFetch;
      if (proto?.open === wrappedOpen) proto.open = originalOpen;
      if (proto?.send === wrappedSend) proto.send = originalSend;
    }
    function stop(code = "observer_stopped") {
      restore();
      if (!finished) {
        finished = true;
        rejectReady(Error(code));
      }
      if (activeReader) {
        void activeReader.cancel().catch(() => {
        });
        activeReader = null;
      }
      if (secret) {
        secret.token.fill(0);
        secret = null;
      }
    }
    async function bodyBytes(body) {
      const value = bytes(body);
      if (value) {
        need2(value.byteLength <= 65536, "observer_body_too_large");
        return value.slice();
      }
      if (body instanceof Blob) {
        need2(body.size <= 65536, "observer_body_too_large");
        return new Uint8Array(await body.arrayBuffer());
      }
      if (body?.getReader) {
        const reader = body.getReader(), parts = [];
        activeReader = reader;
        let total = 0;
        try {
          for (; ; ) {
            const result = await reader.read();
            if (result.done) break;
            total += result.value.byteLength;
            need2(total <= 65536, "observer_body_too_large");
            parts.push(result.value);
          }
          const out = new Uint8Array(total);
          let offset = 0;
          for (const part of parts) {
            out.set(part, offset);
            offset += part.length;
          }
          return out;
        } finally {
          if (activeReader === reader) activeReader = null;
          void reader.cancel().catch(() => {
          });
        }
      }
      throw Error("observer_body_unsupported");
    }
    async function observe(rawUrl, method, body, credentials, acceptedResponse) {
      if (finished || inspecting || method !== "POST") return;
      let url;
      try {
        url = new URL(rawUrl);
      } catch {
        return;
      }
      if (url.protocol !== "https:" || url.username || url.password || url.port || url.hash || !/(^|\.)googlevideo\.com$/.test(url.hostname) || url.pathname !== "/videoplayback") return;
      inspecting = true;
      try {
        need2(++observations <= 16, "normal_request_observation_limit");
        const before = context(), published = new URL(before.response.streamingData?.serverAbrStreamingUrl);
        need2(url.origin === published.origin && url.pathname === published.pathname && !!published.searchParams.get("id") && url.searchParams.get("id") === published.searchParams.get("id"), "observer_server_mismatch");
        const request = sdk.VideoPlaybackAbrRequest.decode(await bodyBytes(body));
        if (finished) return;
        const current = context(), config = current.response.playerConfig?.mediaCommonConfig?.mediaUstreamerRequestConfig?.videoPlaybackUstreamerConfig;
        need2(typeof config === "string" && equal(base64(config), request.videoPlaybackUstreamerConfig || new Uint8Array()), "observer_config_mismatch");
        const token = request.streamerContext?.poToken, client = request.streamerContext?.clientInfo;
        need2(token instanceof Uint8Array && token.length > 0 && token.length < 16384, "observer_token_missing");
        need2(client && Number.isInteger(client.clientName) && typeof client.clientVersion === "string", "observer_client_missing");
        const selected = request.selectedAudioFormatIds || [], formats = current.response.streamingData?.adaptiveFormats || [];
        const matches = /* @__PURE__ */ new Map();
        let observedFormatMatched = false;
        for (const raw of formats) {
          if (!/^audio\/(webm|mp4)(;|$)/.test(raw.mimeType || "")) continue;
          let normalized;
          try {
            normalized = sdk.buildSabrFormat(raw);
          } catch {
            continue;
          }
          if (selected.some((x) => formatKey(x) === formatKey(normalized))) observedFormatMatched = true;
          if (normalized.isDrc || normalized.isVb || normalized.isDubbed || normalized.isAutoDubbed || normalized.isDescriptive || normalized.isSecondary) continue;
          let tags;
          try {
            tags = sdk.FormatXTags.decode(base64(normalized.xtags)).xtags;
          } catch {
            continue;
          }
          if (!tags.some((x) => x.key === "acont" && x.value === "original") || tags.some((x) => x.key === "acont" && x.value !== "original" || ["drc", "vb"].includes(x.key) && x.value === "1")) continue;
          matches.set(formatKey(normalized), normalized);
        }
        need2(observedFormatMatched, "observer_selected_format_mismatch");
        need2(matches.size > 0, "observer_original_format_unproven");
        const candidates = [...matches.values()].sort((a, b) => Number(b.itag === 140) - Number(a.itag === 140) || (b.bitrate || 0) - (a.bitrate || 0) || formatKey(a).localeCompare(formatKey(b)));
        const audioFormat = candidates[0];
        need2(audioFormat.hasAudio && !audioFormat.hasVideo && !audioFormat.hasText, "observer_audio_only_required");
        const durationMs = Number(audioFormat.approxDurationMs) || Math.round(current.video.duration * 1e3);
        need2(Number.isSafeInteger(durationMs) && durationMs > 0 && Math.abs(durationMs - current.video.duration * 1e3) <= 2e3, "observer_duration_mismatch");
        need2(["omit", "same-origin", "include"].includes(credentials), "observer_credentials_mode");
        const accepted = await acceptedResponse;
        if (finished) return;
        context();
        need2(accepted.status === 200 && accepted.contentType === "application/vnd.yt-ump", "normal_request_not_accepted");
        secret = { token: token.slice(), source: {
          videoId,
          isLive: false,
          isPostLive: false,
          noDRM: true,
          durationMs,
          audioFormat,
          serverAbrStreamingUrl: url.href,
          videoPlaybackUstreamerConfig: config,
          clientInfo: client
        }, credentials };
        finished = true;
        restore();
        resolveReady(Object.freeze({
          source: secret.source,
          credentialsMode: credentials,
          getCurrentVideoPoToken: async (id) => {
            context();
            need2(secret && id === videoId, "source_changed");
            return secret.token.slice();
          },
          assertAcceptedContext: async () => {
            context();
            need2(secret, "observer_closed");
            return { accepted: true, videoId };
          },
          fetchInAcceptedContext: (input, init) => {
            context();
            need2(secret, "observer_closed");
            const target = new URL(String(input));
            need2(target.origin === url.origin && target.pathname === "/videoplayback", "source_server_changed");
            return originalFetch.call(scope, input, { ...init, credentials: secret.credentials, redirect: "error" });
          },
          metadata: publicMetadata(current.response, audioFormat),
          close: () => stop("observer_closed")
        }));
      } catch (error) {
        lastReason = /^[a-z0-9_]{1,80}$/.test(error.message || "") ? error.message : "normal_request_unusable";
        if (["source_changed", "response_identity_changed", "source_not_eligible", "normal_request_observation_limit", "source_forbidden", "source_rate_limited"].includes(lastReason)) stop(lastReason);
      } finally {
        inspecting = false;
      }
    }
    function wrappedFetch(input, init) {
      const request = typeof Request !== "undefined" && input instanceof Request ? input : null;
      const method = String(init?.method || request?.method || "GET").toUpperCase();
      const rawUrl = request?.url || String(input), candidate = isCandidate(rawUrl, method);
      let body = init?.body;
      if (candidate && body === void 0 && request) {
        try {
          body = request.clone().body;
        } catch {
        }
      }
      const result = originalFetch.apply(this, arguments);
      if (!candidate) return result;
      const accepted = Promise.resolve(result).then((response) => {
        if (response.status === 403 || response.status === 429) {
          stop(response.status === 403 ? "source_forbidden" : "source_rate_limited");
          throw Error("normal_request_not_accepted");
        }
        return { status: response.status, contentType: (response.headers.get("content-type") || "").split(";")[0] };
      });
      accepted.catch(() => {
      });
      void observe(rawUrl, method, body, init?.credentials || request?.credentials || "same-origin", accepted);
      return result;
    }
    function wrappedOpen(method, url) {
      xhrs.set(this, { method: String(method).toUpperCase(), url: String(url) });
      return originalOpen.apply(this, arguments);
    }
    function isCandidate(rawUrl, method) {
      try {
        const url = new URL(rawUrl), published = new URL(context().response.streamingData?.serverAbrStreamingUrl);
        return !finished && method === "POST" && url.protocol === "https:" && /(^|\.)googlevideo\.com$/.test(url.hostname) && url.pathname === "/videoplayback" && url.origin === published.origin && !!published.searchParams.get("id") && url.searchParams.get("id") === published.searchParams.get("id");
      } catch {
        return false;
      }
    }
    function wrappedSend(body) {
      const request = xhrs.get(this);
      if (request && isCandidate(request.url, request.method)) {
        const accepted = new Promise((resolve) => this.addEventListener("loadend", () => {
          if (this.status === 403 || this.status === 429) stop(this.status === 403 ? "source_forbidden" : "source_rate_limited");
          resolve({ status: this.status, contentType: (this.getResponseHeader("content-type") || "").split(";")[0] });
        }, { once: true }));
        void observe(request.url, request.method, body, this.withCredentials ? "include" : "omit", accepted);
      }
      return originalSend.apply(this, arguments);
    }
    function publicMetadata(response, format) {
      const d = response.videoDetails, m = response.microformat?.playerMicroformatRenderer || {};
      const text = (value, max = 32e3) => typeof value === "string" ? value.slice(0, max) : null;
      return {
        id: videoId,
        webpage_url: `https://www.youtube.com/watch?v=${videoId}`,
        title: text(d.title, 1e3),
        description: text(d.shortDescription),
        channel_id: text(d.channelId, 128),
        channel: text(d.author, 500),
        duration: Math.round(Number(format.approxDurationMs) || context().video.duration * 1e3) / 1e3,
        language: text(format.language, 32),
        upload_date: text(m.uploadDate, 32),
        release_date: text(m.publishDate, 32),
        tags: Array.isArray(d.keywords) ? d.keywords.filter((x) => typeof x === "string").slice(0, 100).map((x) => x.slice(0, 200)) : [],
        thumbnails: (d.thumbnail?.thumbnails || []).filter((x) => {
          try {
            const u = new URL(x.url);
            return u.protocol === "https:" && !u.username && !u.password && !u.port && /(^|\.)ytimg\.com$/.test(u.hostname);
          } catch {
            return false;
          }
        }).slice(0, 10).map((x) => {
          const u = new URL(x.url);
          return { url: u.origin + u.pathname, width: x.width, height: x.height };
        }),
        acquisition_context: "browser_native_sabr",
        native_source_language_basis: "published_original_format"
      };
    }
    context();
    scope.fetch = wrappedFetch;
    if (proto) {
      proto.open = wrappedOpen;
      proto.send = wrappedSend;
    }
    timer = setTimeout(() => stop(lastReason || "normal_request_not_observed"), timeoutMs);
    watcher = setInterval(() => {
      try {
        context();
      } catch (error) {
        stop(error.message);
      }
    }, 250);
    return Object.freeze({ ready, stop });
  }

  // native-finish.js
  async function finishNativeWithProof({ rpc, proof, binding, durationMs, now = Date.now, sleep: sleep2 = (ms) => new Promise((resolve) => setTimeout(resolve, ms)) }) {
    let uncertain = false, reposted = false;
    try {
      await rpc("finish", proof);
    } catch {
      uncertain = true;
    }
    const deadline = now() + Math.max(12e4, durationMs / 3 + 12e4);
    while (now() < deadline) {
      const status = await rpc("status");
      if (status.sourceBindingSha256 !== binding) throw Error("native_status_binding");
      if (status.error) throw Error("native_validation_failed");
      if (status.nativeProof) return status.nativeProof;
      if (uncertain && !reposted && status.state === "receiving") {
        reposted = true;
        try {
          await rpc("finish", proof);
        } catch {
        }
      }
      await sleep2(2e3);
    }
    throw Error("native_validation_timeout");
  }

  // native-main.js
  var active = null;
  var need = (ok, code) => {
    if (!ok) throw Error(code);
  };
  var safe = (error) => /^[a-z0-9_]{1,80}$/.test(error?.message || "") ? error.message : "native_operation_failed";
  var sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
  function classify(code) {
    return /forbidden/.test(code) ? "forbidden" : /rate_limited/.test(code) ? "rate_limited" : /protection_rejected/.test(code) ? "bot_check" : /user_stopped|cancelled/.test(code) ? "aborted" : /checksum|mismatch|gap|integrity|ack/.test(code) ? "integrity" : /fetch|bridge|timeout/.test(code) ? "network" : "protocol";
  }
  function startNativePilot({ nonce, videoId, maxBytes = 64e6 }) {
    need(!active, "native_pilot_already_active");
    need(/^[a-f0-9-]{36}$/.test(nonce) && videoId === "EliqxbbQoRw" && maxBytes === 64e6, "native_pilot_scope");
    const sdk = globalThis.ChannelingNativeSabrV1;
    need(sdk?.sdkVersion === "5.0.1", "native_sdk_missing");
    const controller = new AbortController(), pending = /* @__PURE__ */ new Map();
    let sequence = 0, observer, context, session, jobStarted = false, sourceTimer, bootstrapVideo, resumedPlayback = false;
    const acknowledge = (event) => {
      const data = event.data;
      if (event.source !== window || data?.type !== "channel-native-ack" || data.nonce !== nonce) return;
      const item = pending.get(data.id);
      if (!item) return;
      pending.delete(data.id);
      clearTimeout(item.timer);
      data.error ? item.reject(Error(safe({ message: data.error }))) : item.resolve(data.value);
    };
    window.addEventListener("message", acknowledge);
    const rpc = (operation, value = {}) => new Promise((resolve, reject) => {
      if (pending.size >= 8) {
        reject(Error("native_bridge_backpressure"));
        return;
      }
      const id = sequence++, timer = setTimeout(() => {
        pending.delete(id);
        reject(Error("native_bridge_timeout"));
      }, 2e4);
      pending.set(id, { resolve, reject, timer });
      window.postMessage({ type: "channel-native-rpc", nonce, id, operation, value }, location.origin);
    });
    const state = (phase, extra = {}) => rpc("state", { phase, ...extra });
    const close = () => {
      clearTimeout(sourceTimer);
      observer?.stop();
      context?.close();
      if (resumedPlayback && bootstrapVideo && !bootstrapVideo.paused) bootstrapVideo.pause();
      window.removeEventListener("message", acknowledge);
      for (const item of pending.values()) {
        clearTimeout(item.timer);
        item.reject(Error("native_bridge_closed"));
      }
      pending.clear();
      active = null;
    };
    const run = async () => {
      try {
        await state("observing_normal_request");
        observer = createAcceptedSabrObserver({ sdk, videoId });
        const video = document.getElementById("movie_player")?.querySelector("video");
        need(video, "source_not_ready");
        bootstrapVideo = video;
        if (video.paused) {
          resumedPlayback = true;
          try {
            await video.play();
          } catch {
            throw Error("normal_playback_required");
          }
        }
        context = await observer.ready;
        video.pause();
        const sink = {
          reserve: async (n) => {
            need(Number.isSafeInteger(n) && n > 0 && n <= 1024 * 1024, "native_chunk_size");
          },
          authorizeRequest: (proof) => rpc("request", proof),
          write: async ({ offset, bytes }) => {
            let last;
            for (let position = 0; position < bytes.length; position += 768 * 1024) {
              const piece = bytes.subarray(position, position + 768 * 1024);
              let binary = "";
              for (let i = 0; i < piece.length; i += 8192) binary += String.fromCharCode(...piece.subarray(i, i + 8192));
              last = await rpc("chunk", { offset: offset + position, base64: btoa(binary) });
              need(last.acknowledgedBytes === offset + position + piece.length, "native_chunk_ack");
            }
            return last;
          },
          segment: (proof) => rpc("segment", proof),
          finish: async (proof) => {
            await state("validating_native_audio");
            return finishNativeWithProof({ rpc, proof, binding: session.sourceBinding, durationMs: context.source.durationMs });
          },
          retain: async (proof) => {
            if (jobStarted) await rpc("retain", { error_class: classify(proof.error) });
          }
        };
        session = await sdk.openNativeSabr({
          sdk: sdk.sdk,
          source: context.source,
          fetchInAcceptedContext: context.fetchInAcceptedContext,
          getCurrentVideoPoToken: context.getCurrentVideoPoToken,
          assertAcceptedContext: context.assertAcceptedContext,
          sink,
          maxBytes,
          maxRequests: 1e3,
          requireRequestAuthorization: true,
          signal: controller.signal
        });
        const begin = await rpc("begin", { identity: session.identity, transportKind: "sabr_reassembled", outputBudgetBytes: maxBytes, metadata: context.metadata });
        need(begin.sourceBindingSha256 === session.sourceBinding, "native_begin_binding");
        jobStarted = true;
        await state("downloading_native_audio", { video_id: videoId, source_binding_sha256: session.sourceBinding, identity: session.identity, token_present: true, credentials_mode: context.credentialsMode });
        sourceTimer = setTimeout(() => controller.abort(), 20 * 60 * 1e3);
        const result = await session.run();
        clearTimeout(sourceTimer);
        context.close();
        await state("uploading_verified_native_audio", { bytes: result.bytes });
        const deadline = Date.now() + 20 * 60 * 1e3;
        while (Date.now() < deadline) {
          const status = await rpc("status");
          need(!status.error, "native_upload_retained");
          if (status.driveVerified) {
            await state("drive_verified", { bytes: result.bytes });
            return;
          }
          await sleep(2e3);
        }
        throw Error("native_upload_status_timeout");
      } catch (error) {
        if (session && !session.complete) {
          try {
            await session.abort(safe(error));
          } catch {
          }
        }
        if (jobStarted) {
          try {
            await rpc("retain", { error_class: classify(safe(error)) });
          } catch {
          }
        }
        try {
          await state("held", { error: safe(error), ...session ? { source_binding_sha256: session.sourceBinding, bytes: session.acknowledgedBytes, diagnostics: session.diagnostics() } : {} });
        } catch {
        }
      } finally {
        close();
      }
    };
    active = { stop: () => {
      controller.abort();
      observer?.stop("user_stopped");
      void session?.abort("user_stopped");
    } };
    void run();
    return { started: true, mode: "native_sabr_single_pilot", reencoded: false };
  }
  Object.defineProperty(globalThis, "ChannelingNativePilotV1", { value: Object.freeze({ start: startNativePilot, stop: () => active?.stop() }), configurable: false });
})();
