# Logic

## if

The if module is the phyphox equivalent to the if-statement of a programming language. It takes two inputs a and b and will behave differently depending on the relation of the last values found there. By changing the attributes *less*, *equal* or *greater*, you can decide whether you are looking for a \< b, a = b or a \> b, respectively. If the relation is true, the if-module will write the data from the input *true* to the output, otherwise it will write the data from the input *false*. If you enable multiple attributes, the input *true* is used if any of them is fulfilled, so if you enable *less* and *equal*, a \<= b will write the *true* input to the output, while a \> b writes the *false* input.

Since version 1.4 (phyphox 1.0.6) you may set an input to be of the type *empty*. Effectively, this does not change the output as nothing is written, but can make sense in combination with setting the output to *clear*. In this case, the if module behaves in a somewhat special way as it only clears its output if a matching input is connected. For example, if you set the true input to *empty*, do not connect the false input and set the output to *clear*, it will only clear the output if the condition is true, but leave it alone otherwise. This can be used as a reset condition. Note that since the visual editor does not support reusing buffers, you probably cannot do this there in a reasonable way...

{{spec:analysis/analysis/if}}
