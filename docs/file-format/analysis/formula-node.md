# Formula node

**Available since phyphox file format 1.7 (phyphox 1.1.0)**

The `<input>` and `<output>` tags of the formula module additionally accept the [attributes common to all analysis modules](index.md#analysis-modules-in-general).

For simple calculations, you can either use the math nodes listed on the next pages or write it all in a single formula node. In most cases, when you would need multiple math nodes otherwise, the formula node is faster as it does not need to read and write large buffers multiple times but can do the whole calculation in a single step. However, in some cases, not all options are available in the formula node and the implementations of both versions are not necessarily identical.

```xml
<formula formula="[1]+sqrt((7+[2_])^[3_])">
    <input>singleValue</input>
    <input>multipleValues</input>
    <input>multipleValues2</input>
    <output>result</output>
</formula>
```

The example above takes a single value from the buffer "singleValue" and multiple values from the buffers "multipleValues" and "multipleValues2". These buffers are represented in the formula according to their order as 1, 2 and 3. If only a single value from a buffer is used, it is referred to as \[1\], but if multiple values should be used and the calculation should be repeated for each value and output a result for each value, an underscore is added as in \[2\_\] or \[3\_\]. The example then outputs the result of "A + sqrt((7+B)^C)", with A being the last single value from "singleValue" and B and C being the first value from "multipleValues" and "multipleValues2" respectively. This is repeated with the same single value for A but the second values from "multipleValues" and "multipleValues2" for B and C. In this example, sqrt is a common function across many programming languages and denotes the square root of its parameter.

The formula parser respects brackets ("(" and ")"), understands simple binary operators (+, -, \*, /, % (modulo), ^ (power)) and common functions (sqrt, sin, cos, tan, asin, acos, atan, atan2¹, sinh, cosh, tanh, exp, log, abs, sign, heaviside², round, ceil, floor, min¹², max¹²).

¹ *atan2*, *min* and *max* take two parameters (for example *min(2,5)* yields 2)

² *heaviside*, *min* and *max* are available since file format 1.10 (phyphox [version 1.1.6](../../reference/version-history/1.1.6.md))

Operator precedence is conventional: function calls bind tightest, then ^ (power), then unary minus, then \*, / and %, then + and -. The power operator is right-associative (2^3^2 = 2^(3^2) = 512), while all other binary operators are left-associative (1-2-3 = -4). A unary minus applies to the immediately following operand only, binding tighter than the other binary operators but looser than ^: -2+3 = 1 and -2^2 = -(2^2) = -4. Number literals may use scientific notation with or without an explicit sign in the exponent (1e5, 1e+5, 1e-5).

The *round* function uses C semantics: ties round half away from zero (round(-2.5) = -3) and NaN stays NaN.

A missing or empty *formula* attribute and structurally broken formulas — wrong arity such as min(5) or sin(1,2), dangling operands such as 5+ — reject the file at load.

{{spec:analysis/analysis/formula}}
