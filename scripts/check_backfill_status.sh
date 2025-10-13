#!/bin/bash
# Check the status of the content_tags backfill process

echo "========================================"
echo "Content Tags Backfill Status Check"
echo "========================================"
echo ""

# Check if process is running
echo "1. Process Status:"
if ps aux | grep "backfill_content_tags_junction" | grep -v grep > /dev/null; then
    echo "   ✓ Backfill process IS RUNNING"
    ps aux | grep "backfill_content_tags_junction" | grep -v grep | awk '{print "   PID: "$2" CPU: "$3"% MEM: "$4"% TIME: "$10}'
else
    echo "   ✗ Backfill process NOT running (may have completed or failed)"
fi
echo ""

# Show last 20 lines of log
echo "2. Recent Log Output:"
if [ -f /tmp/backfill_content_tags_full.log ]; then
    tail -20 /tmp/backfill_content_tags_full.log | sed 's/^/   /'
    echo ""
else
    echo "   ✗ Log file not found at /tmp/backfill_content_tags_full.log"
    echo ""
fi

# Check database counts
echo "3. Database Counts:"
export PGPASSWORD=chocolateRainbows858
if psql -h localhost -U genonaut_admin -d genonaut_demo -tA -c "
    SELECT
        content_source,
        TO_CHAR(COUNT(*), '999,999,999') as count,
        MIN(content_id) as min_id,
        MAX(content_id) as max_id
    FROM content_tags
    GROUP BY content_source
    ORDER BY content_source;" 2>/dev/null; then
    echo ""
else
    echo "   ✗ Could not connect to database"
    echo ""
fi

# Show expected vs actual
echo "4. Expected Totals:"
echo "   content_items (regular): ~4,950,000 relationships"
echo "   content_items_auto (auto): ~84,700,000 relationships"
echo "   TOTAL: ~89,650,000 relationships"
echo ""

# Check if complete
echo "5. Completion Check:"
ACTUAL_AUTO=$(psql -h localhost -U genonaut_admin -d genonaut_demo -tAc "SELECT COUNT(*) FROM content_tags WHERE content_source='auto';" 2>/dev/null)
if [ $? -eq 0 ]; then
    if [ "$ACTUAL_AUTO" -gt 80000000 ]; then
        echo "   ✓ Backfill appears COMPLETE! (auto count: $ACTUAL_AUTO)"
    else
        PERCENT=$((ACTUAL_AUTO * 100 / 84700000))
        echo "   ⏳ Backfill in progress: $PERCENT% complete for auto content"
    fi
else
    echo "   ? Could not determine completion status"
fi
echo ""

echo "========================================"
echo "To watch live progress:"
echo "  tail -f /tmp/backfill_content_tags_full.log"
echo "========================================"
