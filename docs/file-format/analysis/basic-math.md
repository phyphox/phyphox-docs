# Basic math

The `<input>` and `<output>` tags of every module on this page additionally accept the [attributes common to all analysis modules](index.md#analysis-modules-in-general).

## abs (absolute)

Calculates the absolute value of a single input element-wise and writes it to a single output buffer. This module will write as many values as there are values in the input buffer.

{{spec:analysis/analysis/abs}}

## add

Calculates the sum of all inputs element-wise and writes it to a single output buffer. This module will write as many values as there are values in the biggest input buffer. If a buffer is shorter than the others (especially if one input is a single value), its last value will be repeated. (Exception: If any buffer is empty, the result will be an empty buffer, too.)

{{spec:analysis/analysis/add}}

## divide

Calculates the quotient of multiple divisors from a single dividend element-wise and writes it to a single output buffer. This module will write as many values as there are values in the biggest input buffer. If a buffer is shorter than the others (especially if one input is a single value), its last value will be repeated. (Exception: If any buffer is empty, the result will be an empty buffer, too.)

For this simple function you can leave out the *as* attribute. If you do so, the first input will be used as dividend and all subsequent values as divisors.

{{spec:analysis/analysis/divide}}

## gcd (greatest common divisor)

Calculates the greatest common divisor of two inputs element-wise and writes it to a single output buffer. This module will write as many values as there are values in the biggest input buffer. If a buffer is shorter than the others (especially if one input is a single value), its last value will be repeated. (Exception: If any buffer is empty, the result will be an empty buffer, too.)

The domain is non-negative integers: fractional values are rounded to the nearest integer with ties rounding half away from zero (like the formula language's round), while negative and non-finite inputs yield NaN, as do values too large to compute with.

{{spec:analysis/analysis/gcd}}

## lcm (least common multiple)

Calculates the least common multiple of two inputs element-wise and writes it to a single output buffer. This module will write as many values as there are values in the biggest input buffer. If a buffer is shorter than the others (especially if one input is a single value), its last value will be repeated. (Exception: If any buffer is empty, the result will be an empty buffer, too.)

The domain is non-negative integers: fractional values are rounded to the nearest integer with ties rounding half away from zero (like the formula language's round), while negative and non-finite inputs yield NaN, as does a result too large to represent. lcm(0, x) is 0 by the usual convention, including lcm(0, 0).

{{spec:analysis/analysis/lcm}}

## log

Calculates the natural logarithm of a single input element-wise and writes it to a single output buffer. This module will write as many values as there are values in the input buffer.

{{spec:analysis/analysis/log}}

## multiply

Calculates the product of all inputs element-wise and writes it to a single output buffer. This module will write as many values as there are values in the biggest input buffer. If a buffer is shorter than the others (especially if one input is a single value), its last value will be repeated. (Exception: If any buffer is empty, the result will be an empty buffer, too.)

{{spec:analysis/analysis/multiply}}

## power

Calculates the power of a base and an exponent element-wise and writes it to a single output buffer. This module will write as many values as there are values in the biggest input buffer. If a buffer is shorter than the others (especially if one input is a single value), its last value will be repeated. (Exception: If any buffer is empty, the result will be an empty buffer, too.)

{{spec:analysis/analysis/power}}

## round

Rounds the values from the single input element-wise and writes the results to a single output buffer. This module will write as many values as there are values in the input buffer. By default it will round to the nearest integer. The attributes *ceil* and *floor* can change that to the nearest larger integer or the nearest smaller integer.

Non-finite values pass through unchanged (NaN stays NaN, infinities stay infinite) and, in the default mode, ties round half away from zero like the formula language's round: round(2.5) is 3 and round(-2.5) is -3.

{{spec:analysis/analysis/round}}

## subtract

Calculates the difference of multiple subtrahends from a single minuend element-wise and writes it to a single output buffer. This module will write as many values as there are values in the biggest input buffer. If a buffer is shorter than the others (especially if one input is a single value), its last value will be repeated. (Exception: If any buffer is empty, the result will be an empty buffer, too.)

For this simple function you can leave out the *as* attribute. If you do so, the first input will be used as minuend and all subsequent values as subtrahends.

{{spec:analysis/analysis/subtract}}
