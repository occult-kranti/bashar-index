# Native SABR SDK bundle

`channeling-native-sabr-v1.iife.js` exposes the frozen `ChannelingNativeSabrV1` namespace in the accepted page. Loading it starts no request. Session material stays in MAIN-world closures; SDK logging is disabled. The controller must explicitly invoke the bounded adapter and the local gateway must admit every source request.

Runtime dependencies are **googlevideo 5.0.1** and **@bufbuild/protobuf 2.17.0**. The build tool is **esbuild 0.25.12**. Exact npm registry integrities, consumed source hashes and output hashes are in `bundle-manifest.json`. Full MIT, Apache-2.0 and BSD-3-Clause notices accompany this bundle in `THIRD_PARTY_NOTICES.txt` and the named license files.

To rebuild, install these exact versions into a separate private directory using the official npm registry and its integrity-checked package lock:

```powershell
npm.cmd install --prefix C:/private-sdk-build --registry https://registry.npmjs.org --ignore-scripts --no-audit --no-fund --save-exact googlevideo@5.0.1 @bufbuild/protobuf@2.17.0 esbuild@0.25.12
node et-channelers/browser_capture_extension/build-native-sdk.mjs --sdk-node-modules C:/private-sdk-build/node_modules
node --test et-channelers/browser_capture_extension/tests/native-sdk-vendor.test.mjs
```

An existing separate esbuild installation may be supplied with `--esbuild-module <path-to-esbuild/lib/main.js>`. The builder performs no downloads and rejects unexpected dependency versions or registry integrities. Keep dependencies and build caches outside the repository; only the reviewed bundle, notices and source-hash manifest belong here. A changed bundle requires a new admitted runtime hash before another pilot.

Offline tests establish API and packaging compatibility. They do not establish acceptance of a source request or completion of a native download. Reassembled SABR output requires segment proofs, full audio validation and verified Drive delivery; a raw SDK snapshot alone does not authorize file resume.
