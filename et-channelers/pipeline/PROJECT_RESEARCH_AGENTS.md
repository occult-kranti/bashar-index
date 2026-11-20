# Local transcripts and API research agents

The latest-20+ collection uses a frozen selection of 1,976 public regular recordings across 101 channels. The collection worker writes verified audio and provenance to Drive. Its local speech supervisor waits for all selected video and channel pairs and for the collection owner to exit. Caption gaps are filled inside the local CUDA environment. A non-English recording with speech gets its original-language transcript and an English translation, with the source edition and timebase preserved.

## Research ownership and billing

All project-funded agents use a single private SQLite budget under the archive root. The operator authorized **$100 total** across project API requests. The configured model is `gpt-5.4-mini-2026-03-17` with standard global service. Each call has a 3,600-token output limit and reserves enough for its full possible context. At the reviewed prices the reservation is $0.3135 per call. The six scheduled calls together have a conservative maximum of $1.881. The ledger charges actual reported usage and releases the balance. Usage elsewhere on the same OpenAI project is billed by OpenAI independently. [Model and token prices](https://developers.openai.com/api/docs/models/gpt-5.4-mini) · [Billing systems](https://help.openai.com/en/articles/9039756-managing-billing-for-chatgpt-and-the-api-platform)

| Stage | Parallel owners | Evidence needed |
|---|---|---|
| Methods review | Study design and source audit | The local collection handoff and an independent reconciliation of all selected Drive receipt identities |
| First corpus review | Corpus statistics and claims/events | Every spoken recording has a verified English view. Individually reviewed non-speech cases and the local TF–IDF, cluster-sensitivity and semantic-retrieval results are bound to the same text generation. |
| Second corpus review | Replication review and synthesis | Both first-round reports, their original evidence and the same frozen generation |

An edition's speech, subtitles, machine translation and publisher transcript retain their source labels. The corpus agents receive aggregate topic tables and a small reproducible set of source-addressable passages. Each finding cites evidence IDs. The second panel sees the first panel's observations and the underlying evidence. Reports and source passages stay in the private archive pending review for publication. The project key funds these API workers. The running Codex conversation and its built-in agent sessions use their own account billing.

## Operation

Run these commands from the `et-channelers` directory. Supply the private archive, the credential **file path**, the speech supervisor's private state directory, and the rclone executable installed on the machine. Configuration records the local credential path. The dispatcher reads the credential only at the first eligible paid call.

~~~powershell
python -m pipeline.research_agent_schedule --root PRIVATE_ROOT configure --credential-file KEY_FILE --asr-state PRIVATE_ASR_STATE --rclone RCLONE_EXECUTABLE
python -m pipeline.research_agent_schedule --root PRIVATE_ROOT status
python -m pipeline.research_agent_schedule --root PRIVATE_ROOT watch
~~~

The Windows research task is registered as `ETChannelers-Latest20-Text-Research`. It resumes at sign-in or on its 15-minute recovery trigger. While downloads are active the worker checks the local completion marker once per minute. One coordinator owns scheduling and at most two independent research calls run concurrently.

The private `research/project-text-agents` folder contains the project-wide budget, status, inputs, provider usage receipts and panel reports. A request first receives a durable reservation and unique dispatch ID. When the connection loses a reply, that reservation stays on the ledger for reconciliation. A restart can finalize an already saved response without sending it again. The client sends the dispatch ID to the API so an uncertain request can be looked up. [Request identification](https://developers.openai.com/api/reference/overview/#debugging-requests)

Further collection at the latest-50 depth remains behind the complete latest-20+ transcription, translation, corpus analysis and second panel review. The existing forecast is 22–28 download hours from that future start. The start date depends on full audio availability and local study completion. [Collection process](COLLECTION_PROCESS.md) · [Roadmap](../ROADMAP.md)
