# Basic math

## abs (absolute)

Calculates the absolute value of a single input element-wise and writes it to a single output buffer. This module will write as many values as there are values in the input buffer.

*value*
:   *input*
:   *as* not required
:   Number of inputs: Exactly one

<!-- -->

*abs*
:   *output*
:   *as* not required

## add

Calculates the sum of all inputs element-wise and writes it to a single output buffer. This module will write as many values as there are values in the biggest input buffer. If a buffer is shorter than the others (especially if one input is a single value), its last value will be repeated. (Exception: If any buffer is empty, the result will be an empty buffer, too.)

*summand*
:   *input*
:   *as* not required
:   Number of inputs: At least one

<!-- -->

*sum*
:   *output*
:   *as* not required

## divide

Calculates the quotient of multiple divisors from a single dividend element-wise and writes it to a single output buffer. This module will write as many values as there are values in the biggest input buffer. If a buffer is shorter than the others (especially if one input is a single value), its last value will be repeated. (Exception: If any buffer is empty, the result will be an empty buffer, too.)

For this simple function you can leave out the *as* attribute. If you do so, the first input will be used as dividend and all subsequent values as divisors.

*dividend*
:   *input*
:   *as* not required, but order matters if left out
:   Number of inputs: Exactly one

*divisor*
:   *input*
:   *as* not required, but order matters if left out
:   Number of inputs: Arbitrary

<!-- -->

*quotient*
:   *output*
:   *as* not required

## gcd (greatest common divisor)

Calculates the greatest common divisor of two inputs element-wise and writes it to a single output buffer. This module will write as many values as there are values in the biggest input buffer. If a buffer is shorter than the others (especially if one input is a single value), its last value will be repeated. (Exception: If any buffer is empty, the result will be an empty buffer, too.)

*value*
:   *input*
:   *as* not required
:   Number of inputs: Exactly two

<!-- -->

*gcd*
:   *output*
:   *as* not required

## lcm (least common multiple)

Calculates the least common multiple of two inputs element-wise and writes it to a single output buffer. This module will write as many values as there are values in the biggest input buffer. If a buffer is shorter than the others (especially if one input is a single value), its last value will be repeated. (Exception: If any buffer is empty, the result will be an empty buffer, too.)

*value*
:   *input*
:   *as* not required
:   Number of inputs: Exactly two

<!-- -->

*lcm*
:   *output*
:   *as* not required

## log

**Available since phyphox file format 1.5 (phyphox 1.0.7)**

Calculates the natural logarithm of a single input element-wise and writes it to a single output buffer. This module will write as many values as there are values in the input buffer.

*value*
:   *input*
:   *as* not required
:   Number of inputs: Exactly one

<!-- -->

*log*
:   *output*
:   *as* not required

## multiply

Calculates the product of all inputs element-wise and writes it to a single output buffer. This module will write as many values as there are values in the biggest input buffer. If a buffer is shorter than the others (especially if one input is a single value), its last value will be repeated. (Exception: If any buffer is empty, the result will be an empty buffer, too.)

*factor*
:   *input*
:   *as* not required
:   Number of inputs: At least one

<!-- -->

*product*
:   *output*
:   *as* not required

## power

Calculates the power of a base and an exponent element-wise and writes it to a single output buffer. This module will write as many values as there are values in the biggest input buffer. If a buffer is shorter than the others (especially if one input is a single value), its last value will be repeated. (Exception: If any buffer is empty, the result will be an empty buffer, too.)

*base*
:   *input*
:   *as* required
:   Number of inputs: Exactly one

*exponent*
:   *input*
:   *as* required
:   Number of inputs: Exactly one

<!-- -->

*power*
:   *output*
:   *as* not required

## round

**Available since phyphox file format 1.5 (phyphox 1.0.7)**

Round the values from the single input element-wise and writes the results to a single output buffer. This module will write as many values as there are values in the input buffer. By default it will round to the nearest integer. The attributes *ceil* and *floor* can change that to the nearest larger integer or the nearest smaller integer.

*floor*
:   *attribute*
:   *optional*, default: false

<!-- -->

*ceil*
:   *attribute*
:   *optional*, default: false

<!-- -->

*value*
:   *input*
:   *as* not required
:   Number of inputs: Exactly one

<!-- -->

*round*
:   *output*
:   *as* not required

## subtract

Calculates the difference of multiple subtrahends from a single minuend element-wise and writes it to a single output buffer. This module will write as many values as there are values in the biggest input buffer. If a buffer is shorter than the others (especially if one input is a single value), its last value will be repeated. (Exception: If any buffer is empty, the result will be an empty buffer, too.)

For this simple function you can leave out the *as* attribute. If you do so, the first input will be used as minuend and all subsequent values as subtrahends.

*minuend*
:   *input*
:   *as* not required, but order matters if left out
:   Number of inputs: Exactly one

*subtrahend*
:   *input*
:   *as* not required, but order matters if left out
:   Number of inputs: Arbitrary

<!-- -->

*difference*
:   *output*
:   *as* not required
