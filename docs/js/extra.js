var render_code = function (device, channel, attr) {
  document.getElementById("offcanvasLabel").innerHTML = device+" / "+channel+" / "+attr;
  document.getElementById("channel_example_iio_attr").innerHTML = get_bash(device,channel,attr);
  document.getElementById("channel_example_iio_python").innerHTML =   get_python(device,channel,attr);
};

var get_bash = function(device,channel,attr) {
return `<pre id="__code_2"><span></span><button class="md-clipboard md-icon" title="Copy to clipboard" data-clipboard-target="#__code_2 > code"></button><code tabindex="0">iio_attr -u ip:analog -c `+device+` `+channel+` `+attr+`</code></pre>`;
}

var get_python = function(device,channel,attr) {
return `<div class="highlight"><pre id="__code_1"><span></span><button class="md-clipboard md-icon" title="Copy to clipboard" data-clipboard-target="#__code_1 > code"></button><code><span class="kn">import</span> <span class="nn">iio</span>
<span class="n">ctx</span> <span class="o">=</span> <span class="n">iio</span><span class="o">.</span><span class="n">Context</span><span class="p">(</span><span class="s2">"ip:analog"</span><span class="p">)</span>
<span class="n">dev</span> <span class="o">=</span> <span class="n">ctx</span><span class="o">.</span><span class="n">find_device</span><span class="p">(</span><span class="s2">"`+device+`"</span><span class="p">)</span>
<span class="n">chan</span> <span class="o">=</span> <span class="n">dev</span><span class="o">.</span><span class="n">find_channel</span><span class="p">(</span><span class="s2">"`+channel+`"</span><span class="p">)</span>
<span class="n">rval</span> <span class="o">=</span> <span class="n">chan</span><span class="o">.</span><span class="n">attr</span><span class="p">[</span><span class="s2">"`+attr+`"</span><span class="p">]</span><span class="o">.</span><span class="n">value</span>
<span class="n">chan</span><span class="o">.</span><span class="n">attr</span><span class="p">[</span><span class="s2">"frequency"</span><span class="p">]</span><span class="o">.</span><span class="n">value</span> <span class="o">=</span> <span class="n">rval</span>
</code></pre></div>`;
}