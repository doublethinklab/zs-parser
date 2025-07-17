## Usage 

Parses data comes from Zeeshuimer, a firefox plugin.
Clone the repo and install it.
```
pip install . 
```
After install, there would be a new command `zs-parser`
The CLI interface supports pipe
```
zs-parser data.ndjson
zs-parser data.json > out.json
cat data.ndjson | zs-parser
head -n 5 data.ndjson | zs-parser > out.json
```
