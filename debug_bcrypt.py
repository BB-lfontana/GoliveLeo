import bcrypt
import sys
print('bcrypt module repr:', repr(bcrypt))
print('__file__:', getattr(bcrypt, '__file__', None))
print('dir contains __about__?:', '__about__' in dir(bcrypt))
print('attrs starting with __:', [a for a in dir(bcrypt) if a.startswith('__')][:20])
print('module type:', type(bcrypt))
print('sys.path sample:', sys.path[:5])
