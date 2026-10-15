# What it needs

This page lists what this solution costs. It covers the libraries, the machine,
the data and the licence.

## 1. What it needs

This is one of the harder solutions in the set to set up. The list below says
what it needs, from the largest cost to the smallest.

- **A deep learning framework.** It needs PyTorch and the RF-DETR package. That
  is a large dependency for a cell whose simplest solution is a page of
  arithmetic.
- **A downloaded weights file.** The borrowed weights are 128 MB. They are
  fetched, not stored with the code. This project cannot make them, so they must
  be trusted.
- **A training set.** The examiner draws and labels it for free, including the
  crowded arrangements. This is the cheap part, and it is why fine-tuning makes
  sense here.
- **Training time.** The fine-tune is the largest cost. It is far shorter than
  training from random numbers. The one fine-tune measured here took 932
  seconds. Other training runs shared the machine, so that is an upper limit.
  The second way was stopped before it finished, so it has no time.
- **Hardware it fits on.** The machine is a laptop. Its graphics processor
  shares memory with the main processor. PyTorch reaches it through Apple's
  Metal Performance Shaders, which PyTorch calls its MPS backend. The code uses
  MPS when it can, and the main processor when it cannot. It prints which one it
  got. There is no NVIDIA card and no CUDA. Shared memory helps the model fit.
  If the model is still too large, a smaller size can be chosen.
- **Weights kept in step with the cell.** Change the camera, the grey shading or
  the range of a kind, and the weights file is out of date. No code test will
  notice.

Running the model is cheap. One pass over one picture takes a small part of the
seconds an arm movement takes. So almost all of this solution's cost is in
building it, not in running it.

The licence is Apache 2.0. It lets you use, change and ship the model with no
duty on the code around it. The two YOLO solutions use the AGPL instead, which
[the licence section of solution
3](../07_a-borrowed-model-as-it-downloads/03_results-and-comparison.md#6-what-it-costs-to-run-and-the-licence)
explains.

[How it compares](06_how-it-compares.md) next weighs these costs against what
the solution scores.

← [A worked example](04_a-worked-example.md) · [How it compares](06_how-it-compares.md) →
