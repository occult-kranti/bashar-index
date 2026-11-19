"""Bounded progress sampling, never a substitute for authority or final-result validation."""
from __future__ import annotations

import errno
import json
from pathlib import Path

from . import progress_observation_io as io


def _absent(path):
    try:
        path.stat()
    except FileNotFoundError as error:
        if error.errno != errno.ENOENT or error.filename is not None and Path(error.filename) != path:
            raise
        return True
    return False


def immutable_result(path):
    with Path(path).open('rb') as stream:
        raw=stream.read(2_000_001)
    if not 0<len(raw)<=2_000_000:
        raise ValueError('immutable_result_size')
    value=json.loads(raw)
    if not isinstance(value,dict):
        raise ValueError('immutable_result_structure')
    return value


class ProgressObserver:
    """Use under the controller dispatch lock for sampling and permit decisions.

    Unstable observations block NEW admission, MEDIA_GO and BODY_GO; existing
    permitted streams and publication can drain. Missing immutable results,
    corrupt JSON, foreign paths and other I/O failures propagate to the owner.
    """
    def __init__(self, *, read_progress=io.read_observation, read_final=immutable_result):
        self.read_progress=read_progress;self.read_final=read_final
        self.unstable=set();self.states={}

    def documents(self, job, *, active=False):
        job=Path(job);video=job.name;progress=job/'progress.json';documents=[]
        present=not _absent(progress)
        if present:
            for attempt in range(1,4):
                try:
                    value=self.read_progress(progress,root=job)
                except io.ObservationChanged:
                    continue
                except FileNotFoundError as error:
                    if error.errno!=errno.ENOENT or error.filename is not None and Path(error.filename)!=progress:
                        raise
                    continue
                if not isinstance(value,dict):
                    raise ValueError('mutable_observation_structure')
                self.unstable.discard(video)
                self.states[video]=dict(state='stable',read_attempts=attempt)
                documents.append(('progress.json',value))
                break
            else:
                self.unstable.add(video)
                self.states[video]=dict(state='unstable_changed_or_missing_snapshot',read_attempts=3)
        elif active:
            self.unstable.add(video)
            self.states[video]=dict(state='unknown_progress_not_yet_present',read_attempts=0)
        final=job/'result.json'
        if not _absent(final):
            # This is deliberately outside the mutable observation catches.
            documents.append(('result.json',self.read_final(final)))
        return documents

    def permits_new_dispatch(self):
        """Advisory gate only; the live grant/provider/size guards still run."""
        return not self.unstable

    def permits_first_bootstrap(self, video, *, started_videos):
        """Own missing first progress is allowed; a started sibling's unknown is not.

        Register the child, test this condition, publish its one durable GO and
        update started_videos atomically under the same dispatch lock.
        """
        return video not in started_videos and not (self.unstable & (set(started_videos)-{video}))

    def accept_validated_closed_terminal(self, video, *, validated_terminal, owned_closure_validated):
        if not isinstance(validated_terminal,dict) or owned_closure_validated is not True:
            raise ValueError('validated_immutable_terminal_and_owned_closure_required')
        self.unstable.discard(video)
        self.states[video]=dict(state='validated_closed_terminal',read_attempts=0)
