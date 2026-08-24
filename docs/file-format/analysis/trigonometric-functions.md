# Trigonometric functions

The `<input>` and `<output>` tags of every module on this page additionally accept the [attributes common to all analysis modules](index.md#analysis-modules-in-general).

## acos

Calculates the inverse cosine of a single input element-wise and writes the resulting angle to a single output buffer. This module will write as many values as there are values in the input buffer. The angle is returned in radians unless degrees are requested using the *deg* attribute.

{{spec:analysis/analysis/acos}}

## asin

Calculates the inverse sine of a single input element-wise and writes the resulting angle to a single output buffer. This module will write as many values as there are values in the input buffer. The angle is returned in radians unless degrees are requested using the *deg* attribute.

{{spec:analysis/analysis/asin}}

## atan

Calculates the inverse tangent of a single input element-wise and writes the resulting angle to a single output buffer. This module will write as many values as there are values in the input buffer. The angle is returned in radians unless degrees are requested using the *deg* attribute.

{{spec:analysis/analysis/atan}}

## atan2

Calculates the two-argument variant of the inverse tangent (corresponding to atan(y/x), see [Wikipedia](https://en.wikipedia.org/wiki/Atan2) for an explanation) element-wise and writes it to a single output buffer. The angle is returned in radians unless degrees are requested using the *deg* attribute. Like the other element-wise modules with several inputs, the output has the length of the longest input and a shorter input repeats its last value; any empty input yields an empty output.

{{inconsistency:atan2-scalar-input}}

{{spec:analysis/analysis/atan2}}

## cos

Calculates the cosine of a single input (in radians) element-wise and writes it to a single output buffer. This module will write as many values as there are values in the input buffer. The module will calculate in radians unless degrees are specified using the *deg* attribute.

{{spec:analysis/analysis/cos}}

## cosh

Calculates the hyperbolic cosine of a single input element-wise and writes it to a single output buffer. This module will write as many values as there are values in the input buffer.

{{spec:analysis/analysis/cosh}}

## sin

Calculates the sine of a single input (in radians) element-wise and writes it to a single output buffer. This module will write as many values as there are values in the input buffer. The module will calculate in radians unless degrees are specified using the *deg* attribute.

{{spec:analysis/analysis/sin}}

## sinh

Calculates the hyperbolic sine of a single input element-wise and writes it to a single output buffer. This module will write as many values as there are values in the input buffer.

{{spec:analysis/analysis/sinh}}

## tan

Calculates the tangent of a single input (in radians) element-wise and writes it to a single output buffer. This module will write as many values as there are values in the input buffer. The module will calculate in radians unless degrees are specified using the *deg* attribute.

{{spec:analysis/analysis/tan}}

## tanh

Calculates the hyperbolic tangent of a single input element-wise and writes it to a single output buffer. This module will write as many values as there are values in the input buffer.

{{spec:analysis/analysis/tanh}}
