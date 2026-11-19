import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'pipeline'))
from interview_guest_discovery import edition_matches, read_episodes, reviewed_appearances


HOST = 'UC' + 'H' * 22
GUEST = 'UC' + 'G' * 22
FEED = 'https://example.org/feed.xml'
GUID = 'show-GUID-1'
EPISODE = ('<item><title>Two Voices &amp; Angels</title><guid>' + GUID + '</guid>'
           '<pubDate>Thu, 19 Nov 2026 08:00:00 -0500</pubDate><i:episode>12</i:episode>'
           '<i:duration>1:03</i:duration><enclosure url="https://example.org/audio.mp3" length="8700" '
           'type="audio/mpeg"/><p:transcript url="https://example.org/transcript.vtt" type="text/vtt"/></item>')
PREFIX = ('<rss xmlns:i="http://www.itunes.com/dtds/podcast-1.0.dtd" '
          'xmlns:p="https://podcastindex.org/namespace/1.0"><channel>'
          '<title>Host interview show</title><language>en</language>')
ROW = {'video_id':'aaaaaaaaaaa','channel_dir':'host','title':'Two voices & Angels',
       'duration_s':64,'tab':'videos','observed_primary_channel_id':HOST,
       'expected_channel_id':HOST,'regular_listing_rank':1}


class InterviewGuestDiscoveryTests(unittest.TestCase):
    def read(self, *items, directory=()):
        return read_episodes((PREFIX + ''.join(items) + '</channel></rss>').encode(), FEED, directory=directory)

    def test_directory_slug_and_publisher_language_are_not_identity(self):
        decoy = {'kind':'podcast-episode','episodeGuid':'wrong','trackName':'Two Voices & Angels',
                 'trackViewUrl':'https://podcasts.apple.com/episode-wrong'}
        matched = dict(decoy, episodeGuid=GUID, trackViewUrl='https://podcasts.apple.com/episode-actual')
        row = self.read(EPISODE,directory=[decoy,matched])[GUID]
        self.assertEqual(row['episode_url'], matched['trackViewUrl'])
        self.assertEqual((row['show_language'],row['transcripts'][0]['language']), ('en',None))
        self.assertEqual(row['duration_seconds'],63)

    def test_display_episode_suffix_requires_agreeing_publisher_numbers_and_duration(self):
        episode = EPISODE.replace('<i:episode>', '<i:season>2</i:season><i:episode>')
        eps = self.read(episode)
        listing = dict(ROW, title='Two Voices & Angels | EP 2-012')
        def matches(rows, item=listing):
            return edition_matches(rows, {'channel_id':HOST, 'items':[item]})
        self.assertEqual([m['episode']['guid'] for m in matches(eps)], [GUID])
        self.assertEqual(matches(eps, dict(listing, title='Two Voices & Angels | EP2-013')), [])
        self.assertEqual(matches(eps, dict(listing, duration_s=300)), [])
        self.assertEqual(matches(self.read(EPISODE)), [])
        self.assertEqual(matches(self.read(episode, episode.replace(GUID, 'another-guid'))), [])

    def test_shared_ordinal_allowed_duplicate_guid_rejected(self):
        a=self.read(EPISODE,EPISODE.replace(GUID,'another'))
        self.assertEqual(len(a),2)
        with self.assertRaises(ValueError):
            self.read(EPISODE,EPISODE)

    def test_edition_join_requires_unique_compatible_full_titles_and_owner(self):
        eps=self.read(EPISODE)
        def match(*rows):
            return edition_matches(eps,{'channel_id':HOST,'items':list(rows)})
        self.assertEqual(match(ROW)[0]['duration_difference_s'],1)
        self.assertEqual(match(dict(ROW,duration_s=160)),[])
        self.assertEqual(match(ROW,dict(ROW,video_id='bbbbbbbbbbb')),[])
        with self.assertRaises(ValueError):
            match(dict(ROW,observed_primary_channel_id=GUEST))
        with self.assertRaises(ValueError):
            match(dict(ROW,tab='shorts'))

    def test_shared_creator_channel_allows_two_distinct_people(self):
        eps = self.read(EPISODE)
        first={'guest':'Ada','guid':GUID,'channel_id':GUEST,'status':'confirmed',
               'role_url':'https://example.org/bio','owner_url':'https://example.org/show',
               'role_evidence':'The creator describes receiving messages.'}
        rows=reviewed_appearances(eps,[first,dict(first,guest='Ben')],HOST)
        self.assertEqual({r['guest'] for r in rows}, {'Ada','Ben'})
        self.assertEqual(len({r['channel_id'] for r in rows}),1)
        with self.assertRaises(ValueError):
            reviewed_appearances(eps,[first,first],HOST)
        with self.assertRaises(ValueError):
            reviewed_appearances(eps,[dict(first,channel_id=HOST)],HOST)
        with self.assertRaises(ValueError):
            reviewed_appearances(eps,[dict(first,role_url='https://example.org/r?token=secret')],HOST)
        role_only=dict(first,status='role_confirmed_channel_unresolved',channel_id='',owner_url='')
        self.assertEqual(reviewed_appearances(eps,[role_only],HOST)[0]['channel_url'],'')
        with self.assertRaises(ValueError):
            reviewed_appearances(eps,[dict(role_only,channel_id=GUEST)],HOST)
