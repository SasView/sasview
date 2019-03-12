import math


def toX(x, y=None):
    """
    This function is used to load value on Plottable.View

    :param x: Float value

    :return: x

    """
    return x


def toX_pos(x, y=None):
    """
    This function is used to load value on Plottable.View

    :param x: Float value

    :return: x

    """
    if not x > 0:
        raise ValueError("Transformation only accepts positive values.")
    else:
        return x


def toX2(x, y=None):
    """
    This function is used to load value on Plottable.View

    Calculate x^(2)

    :param x: float value

    """
    return x * x


def fromX2(x, y=None):
    """
    This function is used to load value on Plottable.View
    Calculate square root of x

    :param x: float value

    """
    if not x >= 0:
        raise ValueError("square root of a negative value ")
    else:
        return math.sqrt(x)


def toX4(x, y=None):
    """
    This function is used to load value on Plottable.View

    Calculate x^(4)

    :param x: float value

    """
    return x * x * x * x


def fromX4(x, y=None):
    """
    This function is used to load value on Plottable.View
    Calculate square root of x

    :param x: float value

    """
    if not x >= 0:
        raise ValueError("double square root of a negative value ")
    else:
        return math.sqrt(math.sqrt(x))


def toLogX(x, y=None):
    """
    This function is used to load value on Plottable.View
    calculate log x

    :param x: float value

    """
    if not x > 0:
        raise ValueError("Log(x)of a negative value ")
    else:
        return math.log(x)

def toOneOverX(x, y=None):
    """
    """
    if x != 0:
        return 1 / x
    else:
        raise ValueError("cannot divide by zero")


def toOneOverSqrtX(y, x=None):
    """
    """
    if y > 0:
        return 1 / math.sqrt(y)
    else:
        raise ValueError("transform.toOneOverSqrtX: cannot be computed")


def toLogYX2(y, x):
    """
    """
    if (y * (x ** 2)) > 0:
        return math.log(y * (x ** 2))
    else:
        raise ValueError("transform.toLogYX2: cannot be computed")


def toLogYX4(y, x):
    """
    """
    if (math.pow(x, 4) * y) > 0:
        return math.log(math.pow(x, 4) * y)
    else:
        raise ValueError("transform.toLogYX4: input error")


def toYX4(y, x):
    """
    """
    return math.pow(x, 4) * y

def toYX2(y, x):
    """
    """
    return math.pow(x, 2) * y

def toLogXY(y, x):
    """
    This function is used to load value on Plottable.View
    calculate log x

    :param x: float value

    """
    if not (x * y) > 0:
        raise ValueError("Log(X*Y)of a negative value ")
    else:
        return math.log(x * y)


def errToX(x, y=None, dx=None, dy=None):
    """
    calculate error of x**2

    :param x: float value
    :param dx: float value

    """
    if dx is None:
        dx = 0
    return dx


def errToX_pos(x, y=None, dx=None, dy=None):
    """
    calculate error of x**2

    :param x: float value
    :param dx: float value

    """
    if dx is None:
        dx = 0
    return dx


def errToX2(x, y=None, dx=None, dy=None):
    """
    calculate error of x**2

    :param x: float value
    :param dx: float value

    """
    if  dx is not None:
        err = 2 * x * dx
        return math.fabs(err)
    else:
        return 0.0


def errFromX2(x, y=None, dx=None, dy=None):
    """
    calculate error of sqrt(x)

    :param x: float value
    :param dx: float value

    """
    if x > 0:
        if dx is not None:
            err = dx / (2 * math.sqrt(x))
        else:
            err = 0
        return math.fabs(err)
    else:
        msg = "transform.errFromX2: can't compute error of negative x"
        raise ValueError(msg)


def errToX4(x, y=None, dx=None, dy=None):
    """
    calculate error of x**4

    :param x: float value
    :param dx: float value

    """
    if dx is not None:
        err = 4 * math.pow(x, 3) * dx
        return math.fabs(err)
    else:
        return 0.0


def errFromX4(x, y=None, dx=None, dy=None):
    """
    calculate error of x^1/4

    :param x: float value
    :param dx: float value

    """
    if x > 0:
        if dx is not None:
            err = dx / (4 * math.pow(x, 3 / 4))
        else:
            err = 0
        return math.fabs(err)
    else:
        msg = "transform.errFromX4: can't compute error of negative x"
        raise ValueError(msg)


def errToLog10X(x, y=None, dx=None, dy=None):
    """
    calculate error of Log(x)

    :param x: float value
    :param dx: float value

    """
    if dx is None:
        dx = 0

    # Check that the point on the graph is positive
    # within errors
    if not (x - dx) > 0:
        msg = "Transformation does not accept"
        msg += " point that are consistent with zero."
        raise ValueError(msg)
    if x != 0:
        dx = dx / (x * math.log(10))
    else:
        raise ValueError("errToLogX: divide by zero")
    return dx


def errToLogX(x, y=None, dx=None, dy=None):
    """
    calculate error of Log(x)

    :param x: float value
    :param dx: float value

    """
    if dx is None:
        dx = 0

    # Check that the x point on the graph is zero
    if x != 0:
        dx = dx / x
    else:
        raise ValueError("errToLogX: divide by zero")
    return dx


def errToYX2(y, x, dy=None, dx=None):
    """
    """
    if dx is None:
        dx = 0
    if dy is None:
        dy = 0
    err = math.sqrt((2 * x * y * dx) ** 2 + ((x ** 2) * dy) ** 2)
    return err


def errToLogXY(x, y, dx=None, dy=None):
    """
    calculate error of Log(xy)

    """
    # Check that the point on the graph is positive
    # within errors
    if not (x - dx) > 0 or not (y - dy) > 0:
        msg = "Transformation does not accept point "
        msg += " that are consistent with zero."
        raise ValueError(msg)
    if x != 0 and y != 0:
        if dx is None:
            dx = 0
        if dy is None:
            dy = 0
        err = (dx / x) ** 2 + (dy / y) ** 2
    else:
        raise ValueError("cannot compute this error")

    return math.sqrt(math.fabs(err))


def errToLogYX2(y, x, dy=None, dx=None):
    """
    calculate error of Log(yx**2)

    """
    # Check that the point on the graph is positive
    # within errors
    if not (x - dx) > 0 or not (y - dy) > 0:
        msg = "Transformation does not accept point"
        msg += " that are consistent with zero."
        raise ValueError(msg)
    if x > 0 and y > 0:
        if dx is None:
            dx = 0
        if dy is None:
            dy = 0
        err = (2.0 * dx / x) ** 2 + (dy / y) ** 2
    else:
        raise ValueError("cannot compute this error")
    return math.sqrt(math.fabs(err))


def errOneOverX(x, y=None, dx=None, dy=None):
    """
    calculate error on 1/x

    """
    if x != 0:
        if dx is None:
            dx = 0
        err = dx / x ** 2
    else:
        raise ValueError("Cannot compute this error")
    return math.fabs(err)


def errOneOverSqrtX(x, y=None, dx=None, dy=None):
    """
    Calculate error on 1/sqrt(x)

    """
    if x > 0:
        if dx is None:
            dx = 0
        err = -1 / 2 * math.pow(x, -3.0 / 2.0) * dx
    else:
        raise ValueError("Cannot compute this error")
    return math.fabs(err)


def errToLogYX4(y, x, dy=None, dx=None):
    """
    error for ln(y*x^(4))

    :param x: float value

    """
    # Check that the point on the graph is positive
    # within errors
    if (not (x - dx) > 0) or (not (y - dy) > 0):
        msg = "Transformation does not accept point "
        msg += " that are consistent with zero."
        raise ValueError(msg)
    if dx is None:
        dx = 0
    if dy is None:
        dy = 0
    err = math.sqrt((4.0 * dx / x) ** 2 + (dy / y) ** 2)
    return err


def errToYX4(y, x, dy=None, dx=None):
    """
    error for (y*x^(4))

    :param x: float value

    """
    # Check that the point on the graph is positive
    # within errors

    if dx is None:
        dx = 0
    if dy is None:
        dy = 0
    err = math.sqrt((dy * pow(x, 4)) ** 2 + (4 * y * dx * math.pow(x, 3)) ** 2)
    return err
