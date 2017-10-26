def enum(*sequential, **named):
    enums = dict(list(zip(sequential, list(range(len(sequential))))), **named)
    return type('Enum', (), enums)

WIDGETS = enum( 'W_FILENAME',           #0
                'W_QMIN',               #1
                'W_QMAX',               #2
                'W_BACKGROUND',         #3
                'W_SCALE',              #4
                'W_CONTRAST',           #5
                'W_EX_QMIN',            #6
                'W_EX_QMAX',            #7
                'W_ENABLE_LOWQ',        #8
                'W_ENABLE_HIGHQ',       #9
                'W_NPTS_LOWQ',          #10
                'W_NPTS_HIGHQ',         #11
                'W_LOWQ_GUINIER',       #12
                'W_LOWQ_POWER',         #13
                'W_LOWQ_FIT',           #14
                'W_LOWQ_FIX',           #15
                'W_LOWQ_POWER_VALUE',   #16
                'W_HIGHQ_FIT',          #17
                'W_HIGHQ_FIX',          #18
                'W_HIGHQ_POWER_VALUE',  #19
                # results
                'W_VOLUME_FRACTION',
                'W_VOLUME_FRACTION_ERR',
                'W_SPECIFIC_SURFACE',
                'W_SPECIFIC_SURFACE_ERR',
                'W_INVARIANT',
                'W_INVARIANT_ERR',
                # for the details widget
                'D_TOTAL_QSTAR',
                'D_TOTAL_QSTAR_ERR',
                'D_LOW_QSTAR',
                'D_LOW_QSTAR_ERR',
                'D_HIGH_QSTAR',
                'D_HIGH_QSTAR_ERR',
)
