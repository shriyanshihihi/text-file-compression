# Benchmark results

| file | original B | compressed B | reduction | Huffman ratio | fixed-k ratio | zlib-9 ratio | entropy b/sym | Huffman b/sym | enc s | dec s | lossless |
|---|---|---|---|---|---|---|---|---|---|---|---|
| catalog.xml | 85782 | 52108 | 39.3% | 1.65x | 1.33x | 6.10x | 4.82 | 4.85 | 0.019 | 0.095 | yes |
| notes.txt | 44124 | 23762 | 46.1% | 1.86x | 1.33x | 4.73x | 4.27 | 4.30 | 0.010 | 0.043 | yes |
| project_source.py.txt | 18847 | 11059 | 41.3% | 1.70x | 1.14x | 3.02x | 4.62 | 4.64 | 0.005 | 0.020 | yes |
| users.json | 90824 | 47834 | 47.3% | 1.90x | 1.14x | 6.53x | 4.16 | 4.21 | 0.020 | 0.088 | yes |

**Average reduction: 43.5%  |  average Huffman ratio vs 8-bit ASCII: 1.78x**

_Measured on the SYNTHETIC demo files in sample_data/ (plus this project's own source). Not the original CV dataset._
