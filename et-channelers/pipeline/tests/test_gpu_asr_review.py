import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from pipeline import gpu_asr as base, gpu_asr_review as review


class SignalFixture:
    def __init__(self, speech_at, sensitive_at=(), conflicting_at=()):
        self.speech_at = set(speech_at)
        self.sensitive_at = set(sensitive_at)
        self.conflicting_at = set(conflicting_at)
        self.detected = []
        self.decoded = 0

    def windows(self, path, duration):
        total = int(duration * base.SAMPLE_RATE)
        for start in range(0,total,30*base.SAMPLE_RATE):
            end = min(start+30*base.SAMPLE_RATE,total)
            self.decoded += end-start
            yield start/base.SAMPLE_RATE, range(start,end)

    def speech(self, signal):
        start = signal.start/base.SAMPLE_RATE
        return signal, len(signal)/base.SAMPLE_RATE if start in self.speech_at else 0

    def sensitive(self, _, signal):
        start = signal.start/base.SAMPLE_RATE
        return signal, len(signal)/base.SAMPLE_RATE if start in self.sensitive_at else 0

    def detect(self, signal):
        start = signal.start/base.SAMPLE_RATE
        self.detected.append(start)
        language = "ja" if start in self.conflicting_at else "en"
        return language,.99,[(language,.99),("fr",.01)]


class PriorSpeechReviews(unittest.TestCase):
    def scan(self, runtime, duration):
        job={"duration_seconds":duration,"declared_audio_language":"und","metadata_content_flags":{}}
        return review.scan_language(runtime,Path("synthetic"),job,lambda:None,relaxed=runtime.sensitive)

    def test_full_scan_resolves_short_spoken_passage_in_long_intro_and_outro(self):
        runtime=SignalFixture([210,220,230])
        result=self.scan(runtime,405)
        self.assertEqual((result["status"],result["language"]),("accepted","en"))
        self.assertEqual(result["fully_scanned_samples"],405*base.SAMPLE_RATE)
        self.assertEqual(runtime.detected,[210,220,230])
        self.assertEqual(len(result["probes"]),41)
        self.assertFalse(result["no_speech_finding_established"])

    def test_sensitive_only_or_conflicting_music_probes_cannot_yield_guessed_text(self):
        for runtime in (SignalFixture([],sensitive_at=[10]),SignalFixture([],sensitive_at=[10,40]),
                        SignalFixture([10,20,30],conflicting_at=[20]), SignalFixture([])):
            result=self.scan(runtime,65)
            self.assertEqual(result["status"],"held")
            self.assertFalse(result["no_speech_finding_established"])
        accepted=self.scan(SignalFixture([],sensitive_at=[0,10,20]),65)
        self.assertEqual(accepted["status"],"accepted")
        self.assertTrue(accepted["only_sensitive_strong_probes"])

    def test_separate_exact_source_hold_metadata_and_retained_file_bindings(self):
        with TemporaryDirectory() as folder:
            root=Path(folder)
            audio=root/"a";meta=root/"m"
            audio.write_bytes(b"audio");meta.write_bytes(b"metadata")
            def obj(path):
                return {**base.hashes(path),"drive_id":"drive-"+path.name,"remote":"drive:audio/"+path.name}
            wanted={"video_id":"12345678901","channel_dir":"creator","edition":"native_youtube_audio",
                    "selection_sha256":"f"*64,"status":"needs_post_collection_lexical_review",
                    "audio":obj(audio),"metadata":obj(meta),"retained_audio":"a","retained_metadata":"m",
                    "prior_hold_reason":"language_confidence_insufficient"}
            old={"video_id":wanted["video_id"],"status":"held","semantic_text_generated":False,
                 "decision":{"status":"held","reason":wanted["prior_hold_reason"]},
                 "source_audio_sha256":wanted["audio"]["sha256"],"source_audio_drive_id":"drive-a"}
            hold=root/"prior.json";hold.write_bytes(base.encoded(old))
            wanted["existing_hold"]={**base.hashes(hold),"path":"prior.json"}
            manifest=root/"review.json"
            manifest.write_bytes(base.encoded({"schema_version":1,"selection_sha256":"f"*64,"recordings":[wanted]}))
            digest=hashlib.sha256(manifest.read_bytes()).hexdigest()
            entry=review.read_plan(root,manifest,digest,"f"*64)[wanted["video_id"]]
            self.assertTrue(review.matches(entry,{"source_type":"native_youtube_audio",**wanted}))
            self.assertEqual(review.retained_pair(root,entry),{"audio":audio,"metadata":meta})
            audio.write_bytes(b"changed")
            with self.assertRaisesRegex(base.AsrError,"retained_review_source_changed"):
                review.retained_pair(root,entry)
            hold.write_bytes(base.encoded({**old,"source_audio_drive_id":"foreign"}))
            with self.assertRaisesRegex(base.AsrError,"review_hold_changed"):
                review.read_plan(root,manifest,digest,"f"*64)
