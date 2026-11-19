import unittest

from pipeline.publisher_episode_audio import compare_feed_extent, compare_mp3_feed_extent, inspect_mp3_episode


class PublisherEpisodeAudioTests(unittest.TestCase):
    def test_explicit_id3_extent_does_not_change_http_or_legacy_comparison(self):
        # Retained complete publisher response: packet duration is independently
        # counted; the parsed artwork/tag is not additional MPEG audio.
        values = dict(advertised_bytes=58_628_388, delivered_bytes=62_121_234,
            advertised_seconds=3664, measured_seconds=3873.28, bitrate=128000,
            http_length=62_121_234)
        with self.assertRaises(ValueError):
            compare_feed_extent(**values)
        result = compare_mp3_feed_extent(**values, delivered_id3_bytes=148_757)
        self.assertEqual(result['delivered_object_bytes'], values['http_length'])
        self.assertEqual(result['delivered_audio_extent_bytes'], 61_972_477)
        self.assertIsNone(result['advertised_metadata_bytes'])
        self.assertAlmostEqual(result['seconds_from_extra_bytes'], 209.0055625)
        for changed in ({'http_length':62_121_233}, {'delivered_id3_bytes':-1},
                        {'delivered_id3_bytes':True}, {'delivered_id3_bytes':5_000_001},
                        {'measured_seconds':3700}, {'measured_seconds':float('nan')}):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                compare_mp3_feed_extent(**{**values, 'delivered_id3_bytes':148_757, **changed})

    def test_http_enclosure_can_have_additional_publisher_audio(self):
        values = dict(advertised_bytes=69615178, delivered_bytes=71994204,
                      advertised_seconds=2230, measured_seconds=2329.0,
                      bitrate=192000, http_length=71994204)
        result = compare_feed_extent(**values)
        self.assertEqual(result['basis'], 'longer_publisher_enclosure')
        self.assertAlmostEqual(result['extra_seconds'], 99)
        for changed in ({'http_length':71994203}, {'measured_seconds':2260},
                        {'measured_seconds':2200}, {'bitrate':0}, {'measured_seconds':float('nan')}):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                compare_feed_extent(**{**values, **changed})

    def setUp(self):
        self.audio = {'codec_type':'audio','codec_name':'mp3','sample_rate':'48000','nb_read_packets':'1000','channels':2,'duration':'24.0'}
        self.cover = {'codec_type':'video','codec_name':'mjpeg','disposition':{'attached_pic':1},'nb_read_packets':'1'}

    def test_cover_is_an_image_alongside_one_audio_program(self):
        for streams, images in [([self.audio], []), ([self.cover,self.audio], ['mjpeg'])]:
            result = inspect_mp3_episode({'streams':streams}, 24)
            self.assertEqual(result['seconds'], 24)
            self.assertEqual(result['attached_cover_art_codecs'], images)

    def test_normal_video_extra_audio_and_truncated_program_are_rejected(self):
        for streams in ([self.audio, self.audio], [self.audio, {**self.cover,'disposition':{'attached_pic':0}}],
                        [self.audio, {**self.cover,'nb_read_packets':'15'}], [{**self.audio,'nb_read_packets':'10'}]):
            with self.subTest(streams=streams), self.assertRaises(ValueError):
                inspect_mp3_episode({'streams':streams},24)
