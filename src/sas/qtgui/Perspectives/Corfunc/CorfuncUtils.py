def enum(*sequential, **named):
    enums = dict(zip(sequential, range(len(sequential))), **named)
    return type('Enum', (), enums)

WIDGETS = enum( 'W_QMIN',
                'W_QMAX',
                'W_QCUTOFF',
                'W_BACKGROUND',
                'W_TRANSFORM',
                )
