def enum(*sequential, **named):
    enums = dict(zip(sequential, range(len(sequential))), **named)
    return type('Enum', (), enums)

WIDGETS = enum( 'W_QMIN',
                'W_QMAX',
                'W_QCUTOFF',
                'W_BACKGROUND',
                'W_TRANSFORM',
                'W_GUINIERA',
                'W_GUINIERB',
                'W_PORODK',
                'W_PORODSIGMA',
                'W_CORETHICK',
                'W_INTTHICK',
                'W_HARDBLOCK',
                'W_CRYSTAL',
                'W_POLY',
                'W_PERIOD',
                )
