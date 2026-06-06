# Free the server ports before (re)building so a re-run never hits "address already in use"
for port in 3000 3002; do
  pids=$(lsof -ti tcp:$port 2>/dev/null)
  if [ -n "$pids" ]; then
    echo "Killing process(es) on port $port: $pids"
    kill -9 $pids 2>/dev/null
  fi
done

cd frontend/atlas; npm run build; cd ../../; python3 src/atlas_ui.py --root /Users/brian/Desktop/Project/NEW_WORKSPACE  --workflow-root /Users/brian/Desktop/Project/brian_hw/common_ai_agent/workflow --port 3000 --admin 3002 --exec s
