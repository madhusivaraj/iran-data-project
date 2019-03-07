LOG_DIR="/logs/$(date +%s)"

mkdir -p $LOG_DIR

echo "Log info file $LOG_DIR/tor.log" > torrc

(
    until tor -f torrc; do
        echo "[$(date)] Tor crashed with exit code $?. Restarting." | tee $LOG_DIR/tor-meta.log
        sleep 1
    done
) &

python3 main.py --log-dir $LOG_DIR "$@"
