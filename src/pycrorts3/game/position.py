from collections import namedtuple

Position = namedtuple('Position', 'x, y')


def cardinal_to_euclidean(position, direction):
    x, y = position
    if direction.endswith('UP'):
        y -= 1
    elif direction.endswith('RIGHT'):
        x += 1
    elif direction.endswith('DOWN'):
        y += 1
    elif direction.endswith('LEFT'):
        x -= 1
    else:
        raise ValueError('Invalid direction "%s"' % direction)
    return Position(x, y)
