# Formula node

**Available since phyphox file format 1.7 (phyphox 1.1.0)**

For simple calculations, you can either use the math nodes listed below or write it all in a single formula node. In most cases, when you would need multiple math nodes otherwise, the formula node is faster as it does not need to read and write large buffers multiple times but can do the whole calculation in a single step. However, in some cases, not all options are available in the formula node and the implementations of both versions are not necessarily identical.

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

{{inconsistency:formula-parse-divergences}}

{{inconsistency:formula-round-semantics}}

{{spec:analysis/analysis/formula}}
