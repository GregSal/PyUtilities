'''Initial testing of DVH read
'''
# pylint: disable=anomalous-backslash-in-string
# pylint: disable=logging-fstring-interpolation
#%% Imports
from collections import deque
from typing import Sequence, TypeVar
import logging_tools as lg

T = TypeVar('T')

#%% Logging
logger = lg.config_logger(prefix='read_dvh.file', level='INFO')


#%% Exceptions
class BufferedIteratorWarnings(UserWarning):
    '''Base Warning class for BufferedIterator.'''


class BufferedIteratorException(Exception):
    '''Base Exception class for BufferedIterator.'''

class BufferedIteratorValueError(BufferedIteratorException, ValueError):
    '''Base Exception class for BufferedIterator.'''

class BufferedIteratorEOF(BufferedIteratorException, StopIteration):
    '''Raised when the source supplied to BufferedIterator is exhausted.
    '''

class BufferOverflowWarning(BufferedIteratorWarnings):
    '''Raised when BufferedIterator peak will cause unyielded
        lines to be dropped.
    '''


#%% Classes
class BufferedIterator():
    '''Iterate through sequence allowing for backup and look ahead.
    '''
    def __init__(self, source: Sequence[T], buffer_size=5):
        self.buffer_size = buffer_size
        self.source_gen = iter(source)
        self.previous_items = deque(maxlen=buffer_size)
        self.future_items = deque(maxlen=buffer_size)
        self._step_back = 0
        return

    def get_next_item(self) -> T:
        if len(self.future_items) > 0:
            # Get the next item from the queued items
            next_item = self.future_items.popleft()
            logger.debug(f'Getting item: {next_item}\t from future_items')
        else:
            # Get the next item from the source iterator
            try:
                next_item = self.source_gen.__next__()
            except (StopIteration, RuntimeError) as eof:
                raise BufferedIteratorEOF from eof
            logger.debug(f'Getting item: {next_item}\t from source')
        return next_item

    def __iter__(self) -> T:
        '''Step through a line sequence allowing for retracing steps.
        '''
        eof = False
        while not eof:
            try:
                next_line = self.get_next_item()
            except BufferedIteratorEOF:
                eof = True
            else:
                self.previous_items.append(next_line)
                yield next_line


    @property
    def step_back(self) -> int:
        '''The number of steps backwards to move the iterator pointer.'''
        return self._step_back

    @step_back.setter
    def step_back(self, steps: int):
        '''Move the iterator pointer back the given number of steps.
        '''
        if steps < 0:
            raise BufferedIteratorValueError("Can't step back negative amount")
        if len(self.previous_items) < steps:
            msg = (f"Can't step back {steps} items.\n\t"
                   f"only have {len(self.previous_items)} previous items "
                    "available.")
            raise BufferedIteratorValueError(msg)
        self._step_back = steps
        self.rewind()

    def backup(self, steps: int = 1):
        '''Move the iterator pointer back the given number of steps.
        '''
        self.step_back = steps
        self.rewind()

    def rewind(self):
        for step in range(self._step_back): # pylint: disable=unused-variable
            self._step_back -= 1
            if len(self.previous_items) > 0:
                self.future_items.appendleft(self.previous_items.pop())
        self._step_back = 0

    def skip(self, steps: int = 1):
        '''Move the iterator pointer forward the given number of steps
           dropping the items in between.  The items dropped cannot be
           retrieved with backup or look_back.
        '''
        if steps < 0:
            raise BufferedIteratorValueError("Can't skip negative amount")
        for step in range(steps): # pylint: disable=unused-variable
            self.get_next_item()

    def advance(self, steps: int = 1):
        '''Move the iterator pointer forward the given number of steps
           storing the items in between as if they had been returned.  The
           items passed over can be retrieved with backup or look_back.
        '''
        if steps < 0:
            raise BufferedIteratorValueError("Can't advance a negative amount")
        if steps > self.buffer_size:
            raise BufferOverflowWarning(
                f'Advance {steps} exceeds the buffer_size. Will not be able '
                'to retrieve all skipped items.')
        for step in range(steps):  # pylint: disable=unused-variable
            try:
                next_item = self.get_next_item()
            except BufferedIteratorEOF as eof:
                raise BufferOverflowWarning(
                    f'advance({steps}) exceeds the remaining items available '
                    'in source.  Advancing to the end of source.') from eof
            else:
                self.previous_items.append(next_item)

    def look_back(self, steps: int = 1)->T:
        '''Return the sequence value the given number of steps back.
        '''
        if steps < 0:
            raise BufferedIteratorValueError("Can't look back a negative amount")
        if len(self.previous_items) < steps:
            msg = (f"Can't look back {steps} items.\n\t"
                   f"only have {len(self.previous_items)} previous items "
                    "available.")
            raise BufferedIteratorValueError(msg)
        return self.previous_items[-steps]


    def look_ahead(self, steps: int = 1)->T:
        '''Return the sequence value the given number of steps Ahead.
        '''
        if steps < 0:
            raise BufferedIteratorValueError("Can't look ahead a negative amount")
        read_ahead = steps - len(self.future_items)
        if read_ahead > 0:
            if read_ahead > self.buffer_size:
                raise BufferedIteratorValueError(
                    f'look_ahead({steps}) exceeds the buffer_size. Will not be able '
                    'to retrieve all skipped items.')
            self.advance(read_ahead)
            self.backup(read_ahead)
        return self.future_items[steps-1]
