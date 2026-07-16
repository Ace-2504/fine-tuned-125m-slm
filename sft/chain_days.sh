#!/usr/bin/env bash
# Chain v1 scaling rounds end-to-end: generate -> build -> upload -> train -> report.
# A per-run report (reports/run-NN.{md,json}) is produced for every day.
#
#   ./chain_days.sh 5 10        # days 5..10
#
# Method is FROZEN across the chain (only dataset size grows), so the scaling curve stays
# comparable. Stops on the first failure so a bad round can be inspected rather than compounded.
set -euo pipefail
export PYTHONIOENCODING=utf-8 MSYS_NO_PATHCONV=1

PY="C:/Users/harma/OneDrive/Desktop/python/vizuara/SLM-course/Replicate-the-125M-SLM-Data-Pipeline/.venv/Scripts/python.exe"
BASE="C:/Users/harma/OneDrive/Desktop/python/vizuara/SLM-course/fine-tuned-125m-slm/125M-model-base"
SFT="$BASE/sft"
PAIRS="$BASE/data/sft/pairs.jsonl"

START=${1:-5}
END=${2:-10}
cd "$SFT"

for day in $(seq "$START" "$END"); do
  echo ""
  echo "======================== DAY $day ========================"
  date +"start %H:%M:%S"

  echo "--- 1/5 generate ---"
  "$PY" gen_qa.py --day "$day" | tail -1

  echo "--- 2/5 build ---"
  "$PY" build_dataset.py 2>/dev/null | grep -E "^TRAIN|  task:|  by day"

  echo "--- 3/5 upload ---"
  "$PY" -m modal volume put slm-125m "$PAIRS" /sft/pairs.jsonl --force >/dev/null 2>&1
  echo "uploaded"

  echo "--- 4/5 train ---"
  "$PY" -m modal run modal_sft.py --day "$day" 2>&1 | grep -E "train_wall|SFT-eval ppl|retention ppl"

  echo "--- 5/5 report ---"
  "$PY" make_report.py --day "$day" | tail -2

  date +"end %H:%M:%S"
  echo "DAY $day COMPLETE"
done

echo ""
echo "======== CHAIN COMPLETE: days $START-$END ========"
