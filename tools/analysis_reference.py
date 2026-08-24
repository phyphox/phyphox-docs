#!/usr/bin/env python3
"""Reference computations for the analysis golden vectors.

An authoring aid, not part of the docs build: when writing a case in
corpus/analysis/cases/*.yml, the expected values are computed here and
written into the case file (expected_source: reference). The functions
implement the semantics established by the 2026-08 audit - the behavior
the two app implementations agree on, pinned in spec/analysis.yml and the
per-module notes of docs/file-format/analysis/ - in plain Python, so a
wrong expectation is an error either here or in both apps, never a
platform quirk.

Conventions shared by the multi-input element-wise modules (add, subtract,
multiply, divide, power, gcd, lcm, atan2), verified against Analysis.java
(the module classes named per function) and the iOS module classes:

* Inputs are lists of floats; a fixed value in the XML is a 1-element list.
* If ANY input is empty, the result is empty.
* Otherwise the result has the length of the LONGEST input; shorter inputs
  repeat their last value.
* NaN and Infinity propagate through IEEE arithmetic; nothing is skipped.

Pure Python (math module only) - the vectors are small.
"""

import math

NAN = float("nan")
INF = float("inf")


def _pick(xs, i):
    return xs[min(i, len(xs) - 1)]


def _elementwise(inputs, fold):
    """The shared Android iteration rule (see module docstring)."""
    if any(len(x) == 0 for x in inputs):
        return []
    n = max(len(x) for x in inputs)
    return [fold([_pick(x, i) for x in inputs]) for i in range(n)]


def _map1(xs, f):
    return [f(x) for x in xs]


# ---------------------------------------------------------------- basic math

def add(*inputs):                       # addAM - sequential accumulation,
    def fold(vs):                       # mirroring the apps' operation order
        acc = 0.0
        for v in vs:
            acc += v
        return acc
    return _elementwise(inputs, fold)


def subtract(minuend, *subtrahends):    # subtractAM
    def fold(vs):
        acc = vs[0]
        for v in vs[1:]:
            acc -= v
        return acc
    return _elementwise([minuend, *subtrahends], fold)


def multiply(*inputs):                  # multiplyAM
    def fold(vs):
        acc = 1.0
        for v in vs:
            acc *= v
        return acc
    return _elementwise(inputs, fold)


def divide(dividend, *divisors):        # divideAM
    def fold(vs):
        acc = vs[0]
        for v in vs[1:]:
            try:
                acc = acc / v
            except ZeroDivisionError:
                acc = _ieee_div(acc, v)
        return acc
    return _elementwise([dividend, *divisors], fold)


def _ieee_div(a, b):
    # Python raises on x/0.0 only for... it does not; float division never
    # raises for float operands. Kept for int operands sneaking in.
    return float(a) / float(b) if b != 0 else (
        NAN if a == 0 or math.isnan(a) else math.copysign(INF, a) * math.copysign(1.0, b))


def power(base, exponent):              # powerAM / nativePower
    def fold(vs):
        b, e = vs
        try:
            return math.pow(b, e)
        except (ValueError, OverflowError):
            # math.pow raises where C pow returns NaN/Inf
            if math.isnan(b) or math.isnan(e):
                return NAN
            if b < 0 and not float(e).is_integer():
                return NAN
            if b == 0 and e < 0:
                return INF
            return NAN
    return _elementwise([base, exponent], fold)


def _int_arg(v):
    """gcd/lcm operand: NaN for non-finite, negative or >= 2^64 after
    rounding half away from zero (gcdOfDoubles)."""
    if math.isnan(v) or math.isinf(v) or v < 0:
        return None
    r = math.floor(v + 0.5)             # half away from zero; v >= 0 here
    if r >= 2 ** 64:
        return None
    return int(r)


def gcd(a, b):                          # gcdAM
    def fold(vs):
        ra, rb = _int_arg(vs[0]), _int_arg(vs[1])
        if ra is None or rb is None:
            return NAN
        return float(math.gcd(ra, rb))
    return _elementwise([a, b], fold)


def lcm(a, b):                          # lcmAM
    def fold(vs):
        ra, rb = _int_arg(vs[0]), _int_arg(vs[1])
        if ra is None or rb is None:
            return NAN
        if ra == 0 or rb == 0:
            return 0.0
        r = ra // math.gcd(ra, rb) * rb
        if r >= 2 ** 64:
            return NAN
        return float(r)
    return _elementwise([a, b], fold)


def abs_(xs):                           # absAM
    return _map1(xs, abs)


def round_(xs, floor=False, ceil=False):   # roundAM
    def f(v):
        if math.isnan(v) or math.isinf(v):
            return v
        if floor:                       # floor wins over ceil on both platforms
            return math.floor(v)
        if ceil:
            return math.ceil(v)
        # nearest, ties half away from zero
        return math.floor(v + 0.5) if v >= 0 else math.ceil(v - 0.5)
    return _map1(xs, f)


def log(xs):                            # logAM - natural log, no attribute
    def f(v):
        if math.isnan(v) or v < 0:
            return NAN
        if v == 0:
            return -INF
        return math.log(v)
    return _map1(xs, f)


# ----------------------------------------------------------------- trig

def _trig_forward(xs, fn, deg):
    def f(v):
        if math.isnan(v) or math.isinf(v):
            return NAN
        return fn(math.radians(v) if deg else v)
    return _map1(xs, f)


def sin(xs, deg=False):
    return _trig_forward(xs, math.sin, deg)


def cos(xs, deg=False):
    return _trig_forward(xs, math.cos, deg)


def tan(xs, deg=False):
    return _trig_forward(xs, math.tan, deg)


def sinh(xs):
    def f(v):
        try:
            return math.sinh(v)
        except OverflowError:
            return math.copysign(INF, v)
    return _map1(xs, f)


def cosh(xs):
    def f(v):
        try:
            return math.cosh(v)
        except OverflowError:
            return INF
    return _map1(xs, f)


def tanh(xs):
    return _map1(xs, math.tanh)


def _trig_inverse(xs, fn, deg):
    def f(v):
        try:
            r = fn(v)
        except ValueError:
            return NAN
        return math.degrees(r) if deg else r
    return _map1(xs, f)


def asin(xs, deg=False):
    return _trig_inverse(xs, math.asin, deg)


def acos(xs, deg=False):
    return _trig_inverse(xs, math.acos, deg)


def atan(xs, deg=False):
    return _trig_inverse(xs, math.atan, deg)


def atan2(ys, xs, deg=False):           # atan2AM; y first, x second
    def fold(vs):
        y, x = vs
        if math.isnan(y) or math.isnan(x):
            return NAN
        r = math.atan2(y, x)
        return math.degrees(r) if deg else r
    return _elementwise([ys, xs], fold)


# ------------------------------------------------------------ signal modules

def autocorrelation(y, x=None, min_x=-INF, max_x=INF):   # autocorrelationAM
    """Returns (x_out, y_out). Normalized per lag by the overlap count n-i;
    x made relative to x[0] (lag axis); minX/maxX filter the lag axis with
    inclusive bounds (NaN bounds filter nothing)."""
    n = len(y)
    if x is not None:
        n = min(n, len(x))
        xr = [x[i] - x[0] for i in range(n)]
    else:
        xr = [float(i) for i in range(n)]
    xs, ys = [], []
    for i in range(n):
        if xr[i] < min_x or xr[i] > max_x:
            continue
        s = 0.0
        for j in range(n - i):
            s += y[j] * y[j + i]
        xs.append(xr[i])
        ys.append(s / (n - i))
    return xs, ys


def crosscorrelation(in1, in2):         # crosscorrelationAM (Java path)
    """Raw correlation sums; larger input is a, smaller b (input2 wins a
    tie); output length = len(a) - len(b) (ties give empty output)."""
    if len(in1) > len(in2):
        a, b = in1, in2
    else:
        a, b = in2, in1
    out = []
    for i in range(len(a) - len(b)):
        s = 0.0
        for j in range(len(b)):
            s += a[j + i] * b[j]
        out.append(s)
    return out


def fft(re, im=None):                   # fftAM - unnormalized forward DFT
    """Returns (re_out, im_out), the full complex spectrum, kernel
    e^(-2*pi*i*k*n/N), no 1/N scaling. Golden vectors use power-of-two
    lengths only (fft-non-power-of-two-input is platform-defined)."""
    if im is not None:
        n = min(len(re), len(im))
    else:
        n = len(re)
        im = [0.0] * n
    if n < 2:
        return [], []
    re_out, im_out = [], []
    for k in range(n):
        sr = si = 0.0
        for j in range(n):
            ang = -2.0 * math.pi * k * j / n
            c, s = math.cos(ang), math.sin(ang)
            sr += re[j] * c - im[j] * s
            si += re[j] * s + im[j] * c
        re_out.append(sr)
        im_out.append(si)
    return re_out, im_out


def gausssmooth(y, sigma=3.0):          # gaussSmoothAM
    """Gaussian kernel, half-width round(3 sigma), truncate-and-renormalize
    at the edges. Output length = input length."""
    n = len(y)
    w = int(math.floor(3.0 * sigma + 0.5))
    kernel = {j: math.exp(-(j * j) / (2.0 * sigma * sigma))
              for j in range(-w, w + 1)}
    out = []
    for i in range(n):
        s = norm = 0.0
        for j in range(-w, w + 1):
            if 0 <= i + j < n:
                s += kernel[j] * y[i + j]
                norm += kernel[j]
        out.append(s / norm)
    return out


def loess(x, y, d, xi):                 # loessAM
    """Weighted quadratic fit with tricube weights over |x-xi| <= d.
    Returns (yi0, yi1, yi2), each len(xi); NaN where the 3x3 system is
    singular (fewer than 3 usable points)."""
    if d is None or not math.isfinite(d) or d <= 0:
        return [], [], []
    n = min(len(x), len(y))
    yi0, yi1, yi2 = [], [], []
    for xv in xi:
        sw = swx = swxx = swxxx = swxxxx = 0.0
        swy = swxy = swxxy = 0.0
        for j in range(n):
            if math.isnan(x[j]) or math.isnan(y[j]):
                continue
            dx = x[j] - xv
            if abs(dx) > d:
                continue
            wgt = (1.0 - abs(dx / d) ** 3) ** 3
            sw += wgt
            swx += wgt * dx
            swxx += wgt * dx * dx
            swxxx += wgt * dx ** 3
            swxxxx += wgt * dx ** 4
            swy += wgt * y[j]
            swxy += wgt * dx * y[j]
            swxxy += wgt * dx * dx * y[j]
        det = (sw * (swxx * swxxxx - swxxx * swxxx)
               - swx * (swx * swxxxx - swxx * swxxx)
               + swxx * (swx * swxxx - swxx * swxx))
        if det == 0:
            yi0.append(NAN)
            yi1.append(NAN)
            yi2.append(NAN)
            continue
        a0 = (swy * (swxx * swxxxx - swxxx * swxxx)
              - swxy * (swx * swxxxx - swxx * swxxx)
              + swxxy * (swx * swxxx - swxx * swxx)) / det
        a1 = (sw * (swxy * swxxxx - swxxy * swxxx)
              - swx * (swy * swxxxx - swxxy * swxx)
              + swxx * (swy * swxxx - swxy * swxx)) / det
        a2 = (sw * (swxx * swxxy - swxxx * swxy)
              - swx * (swx * swxxy - swxxx * swy)
              + swxx * (swx * swxy - swxx * swy)) / det
        yi0.append(a0)
        yi1.append(a1)
        yi2.append(a2)
    return yi0, yi1, yi2


def butterworth(y, x, n, cutoff, cutoff_low=0.0):   # butterworthAM
    """Frequency-domain gain: multiplies y[i] by the Butterworth magnitude
    at f = |x[i]|. cutoffLow <= 0 selects lowpass, > 0 bandpass."""
    if any(v is None or math.isnan(v) for v in (n, cutoff)):
        return []
    m = min(len(y), len(x))
    out = []
    for i in range(m):
        f = abs(x[i])
        if math.isnan(f):
            out.append(NAN)
            continue
        if cutoff_low is None or math.isnan(cutoff_low) or cutoff_low <= 0:
            gain = 1.0 / math.sqrt(1.0 + ((f / cutoff) ** 2) ** n)
        elif f == 0:
            gain = 0.0
        else:
            fl, fh = cutoff_low, cutoff
            t = (f * f - fl * fh) / (f * (fh - fl))
            gain = 1.0 / math.sqrt(1.0 + (t * t) ** n)
        out.append(y[i] * gain)
    return out


def differentiate(xs):                  # differentiateAM
    return [xs[i + 1] - xs[i] for i in range(len(xs) - 1)]


def integrate(xs):                      # integrateAM - cumulative sum
    out, acc = [], 0.0
    for v in xs:
        acc += v
        out.append(acc)
    return out


def binning(xs, x0=0.0, dx=1.0):        # binningAM
    """Returns (binStarts, binCounts): left edges, contiguous over the
    occupied span, lower edge inclusive. Bad x0/dx -> empty."""
    if not (math.isfinite(x0) and math.isfinite(dx)) or dx <= 0:
        return [], []
    counts = {}
    for v in xs:
        if not math.isfinite(v):
            continue
        idx = math.floor((v - x0) / dx)
        counts[idx] = counts.get(idx, 0) + 1
    if not counts:
        return [], []
    lo, hi = min(counts), max(counts)
    starts = [x0 + i * dx for i in range(lo, hi + 1)]
    ncounts = [float(counts.get(i, 0)) for i in range(lo, hi + 1)]
    return starts, ncounts


def threshold(y, x=None, thresh=0.0, falling=False):   # thresholdAM
    """Returns the single output value: x of the first strict crossing
    after arming, or NaN. Without x the sample index is used."""
    last_on_trigger_side = None
    for i, v in enumerate(y):
        fires = (v < thresh) if falling else (v > thresh)
        if fires and last_on_trigger_side is False:
            return x[i] if x is not None and i < len(x) else float(i)
        last_on_trigger_side = bool(fires)
    return NAN


def match(*inputs):                     # matchAM
    """Row-wise up to the shortest input; rows with any non-finite value
    dropped. Returns the list of surviving output lists."""
    n = min(len(b) for b in inputs) if inputs else 0
    outs = [[] for _ in inputs]
    for i in range(n):
        if any(not math.isfinite(b[i]) for b in inputs):
            continue
        for k, b in enumerate(inputs):
            outs[k].append(b[i])
    return outs


def rangefilter(groups):                # rangefilterAM
    """groups: list of (values, min, max) with None for absent bounds.
    Inclusive bounds; iteration to the longest input, exhausted inputs
    contribute NaN (which passes). Returns list of output lists."""
    n = max((len(g[0]) for g in groups), default=0)
    outs = [[] for _ in groups]
    for i in range(n):
        row = []
        drop = False
        for values, lo, hi in groups:
            v = values[i] if i < len(values) else NAN
            row.append(v)
            lo = -INF if lo is None else lo
            hi = INF if hi is None else hi
            if v < lo or v > hi:
                drop = True
        if drop:
            continue
        for k, v in enumerate(row):
            outs[k].append(v)
    return outs


def map_(width, min_x, max_x, height, min_y, max_y, xs, ys, zs=None,
         z_mode="average"):             # mapAM
    """Returns (x_out, y_out, z_out): the W*H grid row-major with y outer,
    nearest-gridpoint binning, ties away from zero."""
    if any(v is None or not math.isfinite(v)
           for v in (width, min_x, max_x, height, min_y, max_y)):
        return [], [], []
    w, h = int(width), int(height)
    if w <= 0 or h <= 0:
        return [], [], []
    n = min(len(xs), len(ys)) if zs is None else min(len(xs), len(ys), len(zs))
    csum = [0.0] * (w * h)
    ccount = [0] * (w * h)

    def snap(v, lo, hi, m):
        t = (m - 1) * (v - lo) / (hi - lo)
        t = max(-1.0, min(float(m), t))
        r = math.floor(t + 0.5) if t >= 0 else math.ceil(t - 0.5)
        return int(r)

    for i in range(n):
        z = 1.0 if zs is None else zs[i]
        if not (math.isfinite(xs[i]) and math.isfinite(ys[i])
                and math.isfinite(z)):
            continue
        xi = snap(xs[i], min_x, max_x, w)
        yi = snap(ys[i], min_y, max_y, h)
        if not (0 <= xi < w and 0 <= yi < h):
            continue
        cell = yi * w + xi
        csum[cell] += z
        ccount[cell] += 1
    x_out, y_out, z_out = [], [], []
    for yi in range(h):
        gy = min_y + yi * (max_y - min_y) / (h - 1) if h > 1 else NAN
        for xi in range(w):
            gx = min_x + xi * (max_x - min_x) / (w - 1) if w > 1 else NAN
            x_out.append(gx)
            y_out.append(gy)
            if z_mode == "count":
                z_out.append(float(ccount[yi * w + xi]))
            elif z_mode == "sum":
                z_out.append(csum[yi * w + xi])
            else:
                c = ccount[yi * w + xi]
                z_out.append(csum[yi * w + xi] / c if c else NAN)
    return x_out, y_out, z_out


# --------------------------------------------------------- aggregate modules

def average(xs):                        # averageAM
    """Returns (average, stddev): one value each. Finite values only; no
    finite values -> NaN average; fewer than two -> NaN stddev (sample
    stddev, divide by n-1)."""
    vals = [v for v in xs if math.isfinite(v)]
    if not vals:
        return NAN, NAN
    avg = 0.0
    for v in vals:
        avg += v
    avg /= len(vals)
    if len(vals) < 2:
        return avg, NAN
    var = 0.0
    for v in vals:
        var += (v - avg) ** 2
    return avg, math.sqrt(var / (len(vals) - 1))


def count(xs):                          # countAM - pure filled size
    return [float(len(xs))]


def _extreme(y, x=None, threshold=None, multiple=False, minimum=False):
    """maxAM/minAM. Returns (extreme_list, position_list)."""
    n = len(y) if x is None else min(len(x), len(y))

    def pos(i):
        return x[i] if x is not None else float(i)

    def better(v, cur):
        return (v < cur) if minimum else (v > cur)

    if not multiple:
        cur = INF if minimum else -INF
        curpos = NAN
        found = False
        for i in range(n):
            if better(y[i], cur):
                cur, curpos, found = y[i], pos(i), True
        if not found:
            return [NAN], [NAN]
        return [cur], [curpos]

    thr = 0.0 if threshold is None else threshold
    out_v, out_p = [], []
    cur = INF if minimum else -INF
    curpos = NAN
    open_set = False
    for i in range(n):
        inside = (y[i] <= thr) if minimum else (y[i] >= thr)
        closes = (y[i] > thr) if minimum else (y[i] < thr)
        if closes and open_set:
            out_v.append(cur)
            out_p.append(curpos)
            cur = INF if minimum else -INF
            curpos = NAN
            open_set = False
        if inside:
            if better(y[i], cur):
                cur, curpos = y[i], pos(i)
                open_set = True
    if open_set:
        out_v.append(cur)
        out_p.append(curpos)
    return out_v, out_p


def max_(y, x=None, threshold=None, multiple=False):
    return _extreme(y, x, threshold, multiple, minimum=False)


def min_(y, x=None, threshold=None, multiple=False):
    return _extreme(y, x, threshold, multiple, minimum=True)


def first(*inputs):                     # firstAM - first element per input
    return [[b[0]] if b else [] for b in inputs]


def sort(*inputs, descending=False):    # sortAM - co-sort by input 1
    n = min(len(b) for b in inputs) if inputs else 0
    key = inputs[0][:n]

    def k(i):
        v = key[i]
        return (1, 0.0) if math.isnan(v) else (0, v)   # NaN sorts largest
    order = sorted(range(n), key=k, reverse=descending)
    return [[b[i] for i in order] for b in inputs]


def append_module(*inputs):             # appendAM - concatenation
    out = []
    for b in inputs:
        out.extend(b)
    return out


def const(value=0.0, length=None, out_size=None):   # constGeneratorAM
    n = out_size if length is None else int(length)
    if n is None or n < 0 or (length is not None
                              and not math.isfinite(length)):
        return []
    return [value] * n


def ramp(start, stop, length=None, out_size=None):  # rampGeneratorAM
    if not (math.isfinite(start) and math.isfinite(stop)):
        return []
    n = out_size if length is None else int(length)
    if n is None or n < 0 or (length is not None
                              and not math.isfinite(length)):
        return []
    if n == 1:
        return [start]
    return [start + (stop - start) / (n - 1) * i for i in range(n)]


def reduce(factor, x, y=None, average_x=False, sum_y=False,
           average_y=False):            # reduceAM
    """Returns (x_out, y_out). factor > 1 decimates in chunks of
    round(factor); factor in (0, 1] inflates by round(1/factor)."""
    if not math.isfinite(factor) or factor <= 0:
        return [], []
    n = len(x) if y is None else min(len(x), len(y))
    yy = y if y is not None else [0.0] * n
    x_out, y_out = [], []
    if factor > 1:
        ifac = int(math.floor(factor + 0.5))
        for c0 in range(0, n, ifac):
            chunk = range(c0, min(c0 + ifac, n))
            used = len(chunk)
            if average_x:
                x_out.append(sum(x[i] for i in chunk) / used)
            else:
                x_out.append(x[c0])
            if sum_y or average_y:
                s = sum(yy[i] for i in chunk)
                y_out.append(s / used if average_y else s)
            else:
                y_out.append(yy[c0])
    else:
        ifac = int(math.floor(1.0 / factor + 0.5))
        for i in range(n):
            x_out.extend([x[i]] * ifac)
            y_out.extend([yy[i]] * ifac)
    return x_out, y_out


def split(data, index=None, overlap=0.0):   # splitAM
    n = len(data)
    idx = float(n) if index is None else index
    if not (math.isfinite(idx) and math.isfinite(overlap)):
        return [], []
    limit = int(max(0, min(n, idx)))
    limit2 = int(max(0, min(n, limit - overlap)))
    return data[:limit], data[limit2:]


def subrange(inputs, from_=None, to=None, length=None):   # subrangeAM
    """inputs: list of buffers. Returns list of outputs."""
    for v in (from_, to, length):
        if v is not None and not math.isfinite(v):
            return [[] for _ in inputs]
    start = 0 if from_ is None else max(0, int(from_))
    if length is not None:
        end = start + int(length)
    elif to is not None:
        end = int(to)
    else:
        end = max((len(b) for b in inputs), default=0)
    return [b[start:min(end, len(b))] if start < min(end, len(b)) else []
            for b in inputs]


def interpolate(x, y, xi, method="linear"):   # interpolateAM
    n = min(len(x), len(y))
    out = []
    j = 0                               # persistent, never rewinds
    for v in xi:
        if n == 0:
            out.append(NAN)
            continue
        if n == 1:
            out.append(y[0])
            continue
        while j < n and x[j] < v:
            j += 1
        if j == 0:
            out.append(y[0])
        elif j == n:
            out.append(y[n - 1])
        elif x[j] == v:
            out.append(y[j])
        elif method == "previous":
            out.append(y[j - 1])
        elif method == "next":
            out.append(y[j])
        elif method == "nearest":
            out.append(y[j - 1] if v - x[j - 1] < x[j] - v else y[j])
        else:
            out.append(y[j - 1] + (y[j] - y[j - 1]) * (v - x[j - 1])
                       / (x[j] - x[j - 1]))
    return out


def movingaverage(data, width=None, drop_incomplete=False):  # movingaverageAM
    w = 10 if width is None else int(width)
    if width is not None and (not math.isfinite(width) or width < 0):
        return []
    out = []
    start = w if drop_incomplete else 0
    for i in range(start, len(data)):
        window = [data[k] for k in range(max(i - w, 0), i + 1)
                  if math.isfinite(data[k])]
        out.append(sum(window) / len(window) if window else NAN)
    return out


# ----------------------------------------------------------- logic / special

def if_(a, b, true_branch=None, false_branch=None,
        less=False, equal=False, greater=False):   # ifAM
    """Compares the LAST values of a and b (exact IEEE, no epsilon; NaN
    makes every relation false). Returns (chosen_array, chosen) where
    chosen is 'true', 'false' or None (no branch input -> output stays
    untouched). Empty a or b -> None."""
    if not a or not b:
        return None, None
    va, vb = a[-1], b[-1]
    cond = ((less and va < vb) or (equal and va == vb)
            or (greater and va > vb))
    branch = true_branch if cond else false_branch
    if branch is None:
        return None, "true" if cond else "false"
    return list(branch), "true" if cond else "false"


def timer_prestart():                   # timerAM, experiment never started
    return [0.0]


def periodicity(x, y, dx, overlap=0.0, min_period=None,
                max_period=None):       # periodicityAM
    """Returns (time_out, period_out) per window. Vectors use the
    user-range path (min/max given) with clean interior peaks."""
    n = min(len(x), len(y))
    dxi = int(dx)
    if dxi <= 0:
        return [], []
    ovl = int(overlap)
    t_out, p_out = [], []
    max_clamp = INF
    step = 0
    while step <= n - dxi:
        x1 = max(step - ovl, 0)
        x2 = min(step + dxi + ovl, n)
        lo = 0 if min_period is None else int(math.floor(min_period))
        hi = INF if max_period is None else math.ceil(max_period)
        max_clamp = min(max_clamp, x2 - x1)
        hi = min(hi, max_clamp)
        sums = {}
        for i in range(lo, int(hi)):
            s = 0.0
            cnt = x2 - x1 - i
            if cnt <= 0:
                break
            for j in range(x1, x2 - i):
                s += y[j] * y[j + i]
            sums[i] = s / cnt
        p, best = None, -INF
        for i, s in sums.items():
            if s > best:
                p, best = i, s
        period = NAN
        if (p is not None and p > 0 and (p - 1) in sums and (p + 1) in sums
                and best > 0 and sums[p - 1] > 0 and sums[p + 1] > 0):
            left, right = sums[p - 1], sums[p + 1]
            m = 0.5 * (right - left) / (2 * best - left - right)
            period = (x[x1 + p] + 0.5 * m * (x[x1 + p + 1] - x[x1 + p - 1])
                      - x[x1])
        t_out.append(x[x1])
        p_out.append(period)
        step += dxi
    return t_out, p_out
