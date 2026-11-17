(() => {
  // native-sabr-diagnostics.js
  var SABR_ERROR_KINDS = Object.freeze([
    "none",
    "sdk_stalled",
    "sdk_request_timeout",
    "sdk_reload_handler_missing",
    "sdk_reload_failed",
    "sdk_sabr_error",
    "sdk_protection_rejected",
    "sdk_format_selection_failed",
    "sdk_unknown_error"
  ]);
  var fields = Object.freeze({
    request: {
      playerTimeMs: "n",
      elapsedWallTimeMs: "n",
      timeSinceLastSeek: "n",
      timeSinceLastActionMs: "n",
      enabledTrackTypesBitfield: "n",
      audioTrackIdPresent: "b",
      selectedAudioCount: "n",
      selectedVideoCount: "n",
      initializationCount: "n",
      selectedAudioMatches: "b",
      bufferedRangeCount: "n",
      bufferedStartMs: "n",
      bufferedDurationMs: "n",
      bufferedStartSegment: "n",
      bufferedEndSegment: "n",
      tokenPresent: "b",
      cookiePresent: "b",
      contextCount: "n"
    },
    policy: {
      backoffTimeMs: "n",
      targetAudioReadaheadMs: "n",
      targetVideoReadaheadMs: "n",
      maxTimeSinceLastRequestMs: "n",
      minAudioReadaheadMs: "n",
      minVideoReadaheadMs: "n",
      cookiePresent: "b"
    },
    seek: { timeMs: "n", source: ["client", "server", "unknown"] },
    reload: {},
    protection: { status: "n", maxRetries: "n" },
    format: { type: ["audio", "video", "unknown"], itag: "n", matchesOutput: "b" },
    track: { segmentCount: "n", bufferedMs: "n", endOfStream: "b" },
    response: { status: "n" },
    error: { code: "n" },
    observer_error: {}
  });
  var number = (x) => typeof x === "number" && Number.isFinite(x) && x >= 0 && x <= 1e12;
  var exact = (x, names) => x && typeof x === "object" && !Array.isArray(x) && Object.keys(x).every((k) => names.includes(k));
  function eventValid(e) {
    if (!exact(e, ["kind", "sequence", ...Object.keys(fields[e?.kind] || {})]) || !Object.hasOwn(fields, e.kind) || !Number.isSafeInteger(e.sequence) || e.sequence < 1 || e.sequence > 1e9) return false;
    return Object.entries(e).every(([k, v]) => k === "kind" || k === "sequence" || (fields[e.kind][k] === "n" ? number(v) : fields[e.kind][k] === "b" ? typeof v === "boolean" : fields[e.kind][k]?.includes(v)));
  }
  function validateSabrDiagnostics(x) {
    const kinds = Object.keys(fields);
    if (!exact(x, ["schemaVersion", "errorKind", "counts", "latest", "events"]) || x.schemaVersion !== 1 || !SABR_ERROR_KINDS.includes(x.errorKind) || !exact(x.counts, kinds) || Object.keys(x.counts).length !== kinds.length || !Object.values(x.counts).every((n) => Number.isSafeInteger(n) && n >= 0 && n <= 1e9) || !exact(x.latest, kinds) || !Object.entries(x.latest).every(([k, v]) => v.kind === k && eventValid(v)) || !Array.isArray(x.events) || x.events.length > 16 || !x.events.every(eventValid) || JSON.stringify(x).length > 16e3)
      throw Error("native_diagnostics_schema");
    return x;
  }

  // native-rpc.js
  var need = (ok) => {
    if (!ok) throw Error("native_rpc_schema");
  };
  var integer = (x, max = 64e6) => Number.isSafeInteger(x) && x >= 0 && x <= max;
  var hash = (x) => typeof x === "string" && /^[a-f0-9]{64}$/.test(x);
  var code = (x) => typeof x === "string" && /^[a-z0-9_]{1,80}$/.test(x);
  var keys = (x, required, optional = []) => {
    need(x && typeof x === "object" && !Array.isArray(x));
    need(required.every((k) => Object.hasOwn(x, k)) && Object.keys(x).every((k) => required.includes(k) || optional.includes(k)));
  };
  var text = (x, max) => x === null || typeof x === "string" && x.length <= max && !/(googlevideo\.com|\/videoplayback|\/timedtext|\bbearer\s)/i.test(x);
  function identity(x) {
    keys(x, ["videoId", "itag", "lastModified", "xtags", "mimeType", "durationMs", "language", "codec", "contentLength", "originalBasis", "trackId", "noDRM", "audioOnly"]);
    need(/^[A-Za-z0-9_-]{11}$/.test(x.videoId) && integer(x.itag, 9999) && x.itag > 0 && /^\d{1,30}$/.test(x.lastModified));
    need(typeof x.xtags === "string" && x.xtags.length <= 4096 && /^[A-Za-z0-9_+/=%-]+$/.test(x.xtags));
    need(/^audio\/(mp4|webm)(?:;\s*codecs="[A-Za-z0-9., -]{1,100}")?$/.test(x.mimeType));
    need(integer(x.durationMs, 1e10) && x.durationMs > 0 && (x.contentLength === null || integer(x.contentLength, 1e10) && x.contentLength > 0));
    need((x.language === null || /^[A-Za-z0-9_.-]{1,32}$/.test(x.language)) && /^[A-Za-z0-9_.-]{1,64}$/.test(x.codec));
    need((x.trackId === null || /^[A-Za-z0-9_.=,; -]{1,200}$/.test(x.trackId)) && x.originalBasis === "published_original" && x.noDRM === true && x.audioOnly === true);
  }
  function metadata(x, videoId) {
    keys(x, ["id"], ["webpage_url", "title", "description", "channel_id", "channel", "duration", "language", "upload_date", "release_date", "tags", "thumbnails", "acquisition_context", "native_source_language_basis", "native_source_acceptance"]);
    need(x.id === videoId && (!x.webpage_url || x.webpage_url === `https://www.youtube.com/watch?v=${videoId}`));
    for (const [key, max] of [["title", 1e3], ["description", 32e3], ["channel_id", 128], ["channel", 500], ["language", 32], ["upload_date", 32], ["release_date", 32], ["acquisition_context", 80], ["native_source_language_basis", 80]]) if (x[key] !== void 0) need(text(x[key], max));
    if (x.duration !== void 0) need(typeof x.duration === "number" && Number.isFinite(x.duration) && x.duration > 0 && x.duration <= 1e7);
    if (x.tags !== void 0) need(Array.isArray(x.tags) && x.tags.length <= 100 && x.tags.every((s) => text(s, 200)));
    if (x.native_source_acceptance !== void 0) {
      const a = x.native_source_acceptance;
      keys(a, ["basis", "http_status", "sps_status", "complete_response", "video_id", "same_video", "same_configuration", "request_format_matches_catalog", "observed_at_epoch", "observer_session_id"]);
      need(a.basis === "matching_normal_player_sps1" && a.http_status === 200 && a.sps_status === 1 && a.video_id === videoId && a.complete_response === true && a.same_video === true && a.same_configuration === true && a.request_format_matches_catalog === true && integer(a.observed_at_epoch, 1e11) && a.observed_at_epoch > 0 && typeof a.observer_session_id === "string" && /^[a-f0-9-]{36}$/.test(a.observer_session_id));
    }
    if (x.thumbnails !== void 0) {
      need(Array.isArray(x.thumbnails) && x.thumbnails.length <= 10);
      for (const thumb of x.thumbnails) {
        keys(thumb, ["url"], ["width", "height"]);
        const u = new URL(thumb.url);
        need(u.protocol === "https:" && !u.username && !u.password && !u.port && !u.search && !u.hash && /(^|\.)ytimg\.com$/.test(u.hostname));
        for (const key of ["width", "height"]) if (thumb[key] !== void 0) need(integer(thumb[key], 2e4));
      }
    }
  }
  function validateNativeRpc(operation, value) {
    try {
      need(typeof operation === "string");
      if (operation === "state") {
        keys(value, ["phase"], ["video_id", "source_binding_sha256", "bytes", "token_present", "credentials_mode", "identity", "error", "diagnostics"]);
        need(["observing_normal_request", "downloading_native_audio", "validating_native_audio", "uploading_verified_native_audio", "drive_verified", "held"].includes(value.phase));
        if (value.video_id !== void 0) need(/^[A-Za-z0-9_-]{11}$/.test(value.video_id));
        if (value.source_binding_sha256 !== void 0) need(hash(value.source_binding_sha256));
        if (value.bytes !== void 0) need(integer(value.bytes));
        if (value.error !== void 0) need(code(value.error));
        if (value.token_present !== void 0) need(typeof value.token_present === "boolean");
        if (value.credentials_mode !== void 0) need(["omit", "include", "same-origin"].includes(value.credentials_mode));
        if (value.identity !== void 0) identity(value.identity);
        if (value.diagnostics !== void 0) validateSabrDiagnostics(value.diagnostics);
      } else if (operation === "begin") {
        keys(value, ["identity", "transportKind", "outputBudgetBytes", "metadata"]);
        identity(value.identity);
        metadata(value.metadata, value.identity.videoId);
        need(value.transportKind === "sabr_reassembled" && value.outputBudgetBytes === 64e6);
      } else if (operation === "request") {
        keys(value, ["sourceBindingSha256", "requestSequence"]);
        need(hash(value.sourceBindingSha256) && integer(value.requestSequence, 1e3) && value.requestSequence > 0);
      } else if (operation === "chunk") {
        keys(value, ["offset", "base64"]);
        need(integer(value.offset) && typeof value.base64 === "string" && value.base64.length > 0 && value.base64.length <= 1048576 && /^[A-Za-z0-9+/]*={0,2}$/.test(value.base64));
      } else if (operation === "segment") {
        keys(value, ["number", "initialization", "startTimeMs", "endTimeMs", "declaredBytes", "byteOffset", "emittedBytes", "sha256", "initDiscardedBytes"]);
        need(integer(value.number, 1e6) && typeof value.initialization === "boolean" && hash(value.sha256) && value.initDiscardedBytes === 0);
        for (const key of ["startTimeMs", "endTimeMs"]) need(integer(value[key], 1e10));
        for (const key of ["declaredBytes", "byteOffset", "emittedBytes"]) need(integer(value[key]));
        need(value.declaredBytes > 0 && value.emittedBytes === value.declaredBytes && value.endTimeMs >= value.startTimeMs);
      } else if (operation === "finish") {
        keys(value, ["sourceBinding", "sourceBindingSha256", "bytes", "identity", "nativeProtocol", "transportKind", "container_reassembled", "encoded_audio_not_reencoded", "reencoded", "isLive", "stripDuplicateInit", "protocolEos", "endSegmentNum", "endTimeMs", "segmentCount", "segmentLedgerSha256", "decodeValidationRequired", "driveVerificationRequired"]);
        identity(value.identity);
        need(hash(value.sourceBinding) && value.sourceBinding === value.sourceBindingSha256 && hash(value.segmentLedgerSha256) && integer(value.bytes) && value.bytes > 0);
        need(value.nativeProtocol === "sabr" && value.transportKind === "sabr_reassembled" && value.reencoded === false && value.isLive === false && value.stripDuplicateInit === false);
        for (const key of ["container_reassembled", "encoded_audio_not_reencoded", "protocolEos", "decodeValidationRequired", "driveVerificationRequired"]) need(value[key] === true);
        need(integer(value.endSegmentNum, 1e6) && integer(value.segmentCount, 1e6) && integer(value.endTimeMs, 1e10));
      } else if (operation === "retain") {
        keys(value, ["error_class"]);
        need(["forbidden", "rate_limited", "bot_check", "network", "aborted", "protocol", "integrity"].includes(value.error_class));
      } else if (operation === "status") keys(value, []);
      else need(false);
      need(JSON.stringify(value).length <= (operation === "chunk" ? 105e4 : 262144));
      return value;
    } catch {
      throw Error("native_rpc_schema");
    }
  }

  // native-isolated-bridge.js
  (() => {
    if (globalThis.__channelNativeBridge) return;
    let config = null;
    chrome.runtime.onMessage.addListener((value, sender, reply) => {
      if (sender.id !== chrome.runtime.id || value.target !== "native-isolated") return;
      if (value.type === "configure") {
        config = { nonce: value.nonce };
        reply({ ready: true });
      }
      if (value.type === "clear") {
        config = null;
        reply({ ready: true });
      }
    });
    window.addEventListener("message", (event) => {
      const value = event.data;
      if (event.source !== window || !config || value?.type !== "channel-native-rpc" || value.nonce !== config.nonce || !Number.isSafeInteger(value.id)) return;
      try {
        validateNativeRpc(value.operation, value.value);
      } catch {
        window.postMessage({ type: "channel-native-ack", nonce: value.nonce, id: value.id, error: "native_rpc_schema" }, location.origin);
        return;
      }
      chrome.runtime.sendMessage({ target: "native-background", nonce: config.nonce, id: value.id, operation: value.operation, value: value.value }).then((result) => window.postMessage({ type: "channel-native-ack", nonce: value.nonce, id: value.id, ...result }, location.origin)).catch(() => window.postMessage({ type: "channel-native-ack", nonce: value.nonce, id: value.id, error: "native_bridge_unavailable" }, location.origin));
    });
    globalThis.__channelNativeBridge = true;
  })();
})();
