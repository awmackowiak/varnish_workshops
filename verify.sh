#!/usr/bin/env bash
# Usage: ./verify.sh [1-8]   (no arg = all). Needs the lab running (make up).
# 1-4 need the VCL from the matching exercise (or later); 5-6 need ex5; 8 checks the broken VCLs are fixed.
V=http://localhost:8081
ok=0
fail=0
check() { if [ "$2" = "$3" ]; then
  echo "PASS $1"
  ok=$((ok + 1))
else
  echo "FAIL $1 (expected '$3', got '$2')"
  fail=$((fail + 1))
fi; }
hdr() { curl -sI ${3:+-H "$3"} "$1" | tr -d '\r' | awk -F': ' -v h="$2" 'tolower($1)==tolower(h){print $2}'; }
rnd() { echo "$RANDOM$RANDOM"; }

ex1() {
  local u="$V/static?cb=$(rnd)"
  check "1 first request is MISS" "$(hdr $u X-Cache)" MISS
  check "1 second request is HIT" "$(hdr $u X-Cache)" HIT
}
ex2() {
  local u="$V/time?cb=$(rnd)" a b c
  a=$(curl -s $u)
  sleep 1
  b=$(curl -s $u)
  sleep 6
  curl -s -o /dev/null $u
  sleep 1
  c=$(curl -s $u)
  check "2 /time cached within TTL" "$b" "$a"
  check "2 /time refetched after 5s TTL (stale served once during grace)" "$([ "$c" != "$a" ] && echo yes || echo no)" yes
}
ex3() {
  local u="$V/cookie?cb=$(rnd)"
  curl -s -o /dev/null $u
  check "3 /cookie cached (HIT) after stripping Set-Cookie" "$(hdr $u X-Cache)" HIT
  check "3b Server header removed" "$(hdr $u Server)" ""
  check "3b X-Cache-Hits set" "$([ -n "$(hdr $u X-Cache-Hits)" ] && echo yes || echo no)" yes
}
ex4() {
  local u="$V/static?cb=$(rnd)"
  curl -s -o /dev/null $u
  check "4 cached before purge" "$(hdr $u X-Cache)" HIT
  curl -s -o /dev/null -X PURGE $u
  check "4 PURGE then MISS" "$(hdr $u X-Cache)" MISS
}
ex5() { check "5 balanced across backends" "$(for i in 1 2 3 4 5 6; do curl -s -D - -o /dev/null "$V/nocache?i=$i" | tr -d '\r' | awk -F': ' 'tolower($1)=="x-backend"{print $2}'; done | sort -u | wc -l | tr -d ' ')" 2; }
ex6() {
  curl -s -X POST localhost:8091/toggle >/dev/null
  sleep 8
  check "6 failover: backend2 serves while backend1 down" "$(hdr $V/nocache?f=1 X-Backend)" backend2
  curl -s -X POST localhost:8091/toggle >/dev/null
  sleep 8
}
ex8() {
  local u="$V/static?cb=$(rnd)"
  curl -s -o /dev/null $u
  check "8a /static is cacheable (b1 fixed)" "$(hdr $u X-Cache)" HIT
  check "8b both backends used (b2 fixed)" "$(for i in 1 2 3 4 5 6; do curl -s -D - -o /dev/null "$V/nocache?i=$i" | tr -d '\r' | awk -F': ' 'tolower($1)=="x-backend"{print $2}'; done | sort -u | wc -l | tr -d ' ')" 2
  u="$V/static?cb=$(rnd)"
  curl -s -o /dev/null -H "User-Agent: A" $u
  check "8c HIT regardless of User-Agent (b3 fixed)" "$(hdr $u X-Cache 'User-Agent: B')" HIT
}

if [ -n "$1" ]; then ex$1; else for n in 1 2 3 4 5 6 8; do ex$n; done; fi
echo "passed=$ok failed=$fail"
[ $fail -eq 0 ]
