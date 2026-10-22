# T8 headline result: the bar on t1_1000m

Filed by the forecast planner (Alder Bearing) on 2026-10-21, as soon as the result came in, so it doesn't live only in a session. The run used t8-build 49862a1 and unit t8-fit-t1_1000m-bar (14:25:03Z to 14:57:33Z, 1,912.9 s, peak 915 MB under a 3 GB cap). The other parts are still running and will be reported separately. The output is at ~/Zynergy/forecast-data/t8/fit/ and is not committed.

- t1_1000m_bar.json sha256 fd38cc6f9977fc95ebef7a036c13e1f6539d158cd18f8fc6f9a0b47a3bfe8120
- t1_1000m_bar.npz sha256 3011a6c3fc5f6486b18d21027be6c2b97ce8090503df4fcf5dc1d20345650805

**Verdict (label `verdict`): passed = False.**

| Condition | Passed | Reason, as written by the script |
|---|---|---|
| C1 | False | against T1's stored calendar, skill -0.01108 [-0.01762, -0.00503]; needs the interval wholly above zero |
| C2 | False | against the no-weather model, skill -0.00138 [-0.00405, +0.00086]; needs the interval wholly above zero |
| C3 | False | 173 of 199 swaps at or above the model, p = 0.870; needs p <= 0.05 |
| C4 | False | lichen reports, weather against no-weather, skill +0.00215 [+0.00027, +0.00394]; needs the interval not wholly above zero |

The figures were copied from the output's `bar` field by script. The planner checked the sha256 values against Ash's report, and they match.
