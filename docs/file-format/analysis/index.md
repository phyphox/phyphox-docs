# Analysis

The analysis block describes all the math required for the experiment. Each element within this block is executed consecutively and usually reads from a data-container, performs a mathematical operation on the data and writes the results to another data-container.

In most experiments the analysis block is executed in a loop, so the experiment data is analyzed as fast as possible. However, if you need to acquire a certain amount of data first (mostly when recording from the microphone) or if the results only change if the user changes a parameter, you can define the attributes *sleep*, *dynamicSleep* and/or *onUserInput* to pause the analysis loop.

{{spec:analysis/phyphox/analysis|attributes}}

An earlier attribute `optimization` was removed in phyphox file format 1.10
(phyphox 1.1.6); it barely added any value but increased confusion
significantly. It is ignored if present in an old file.

```xml
<phyphox version="1.0">
    ...
    <analysis sleep="2.0" dynamicSleep="buffer" onUserInput="false">
        <add>
            <input>Buffer1</input>
            <input type="buffer">Buffer 2</input>
            <output>sumBuffer</output>
        </add>
        <divide>
            <input type="value" as="dividend">1</input>
            <input as="divisor">sumBuffer</input>
            <output>inverseSum</output>
        </divide>
    </analysis>
    ...
</phyphox>
```

## Analysis modules in general

Almost all analysis modules take inputs and write their results to an output buffer. All inputs and outputs are defined as *input* and *output* tags within the analysis module. While the output always has to be a data-container, the input may also be a floating point value which can be defined by setting the attribute *type* to *value*. If *type* is not set, it defaults to *buffer* and the given name has to match a data-container. Additionally, the input may be set to the *type* *empty*, which is similar to *value* but represents a constant empty buffer. This only makes sense and is supported for a few modules, which is noted where applicable.

Both inputs and outputs can be given a specific function by the *as* attribute. For many modules this attribute can be omitted if it is obvious. For example, the *add* module takes an arbitrary number of inputs in an arbitrary order (a+b equals b+a), but the *subtract* module needs an explicit mapping for the *minuend* and the *subtrahend* (a-b does not equal b-a). Similarly, a single output does not need to be mapped, while multiple outputs (for example value and position of a maximum in the *max* module) need to be mapped.

Additionally, some analysis modules take parameters that are not dynamically defined, but set as an attribute of the analysis module tag. As an example, the *threshold* module searches for the point at which the input values cross a given threshold and the attribute *falling* can switch it to look for a crossing from larger to smaller values.

**Since file format version 1.10 (phyphox 1.1.6)** all analysis modules support a new attribute that makes it possible to determine whether the module should be executed in each analysis cycle or only in specific cycles. For this, each run of the analysis process (a cycle) is numbered. When the user opens the experiment and **before** they press start, analysis is triggered with the cycle number 0, which can be used to prepare some buffers or fill graphs with defaults. After pressing start, the first cycle is number 1, followed by cycle 2 etc.

You can then set the attribute *cycles* for any analysis module. If not set, the module is executed in every cycle (including 0). If set, it is only executed in the cycles that you specify by a space-separated list. For example, cycles="1 3 42" means that the module is only executed in cycles 1, 3 and 42. You can also define ranges with a simple dash, so cycles="3-6" means that it will be executed in 3, 4, 5 and 6. Open-ended lists can be achieved by simply omitting a number, so cycles="1-" will run in every cycle except for 0 and cycles="-5" will run in every cycle up to and including number 5. As a final example, mixing all these, cycles="0 3 5-7 10-" will run in cycles 0, 3, 5, 6, 7, 10 and then every subsequent cycle.

{{spec:analysis/phyphox/analysis|common}}

{{inconsistency:input-type-empty-case}}

{{inconsistency:analysis-clear-edit-buffers}}

## List of analysis modules

The specific mappings, attributes and functionality of the analysis modules are documented by category:

- [Formula node](formula-node.md)
- [Basic math](basic-math.md)
- [Trigonometric functions](trigonometric-functions.md)
- [Statistics](statistics.md)
- [Advanced math](advanced-math.md)
- [Buffer operations](buffer-operations.md)
- [Data generation](data-generation.md)
- [Logic](logic.md)
- [Other](other.md)
