import time
import random
import sys
import csv
import os
from dataclasses import dataclass
from typing import List, Tuple, Callable, Optional

# Increase recursion limit to reduce chance of recursion errors on large N for merge/quick
sys.setrecursionlimit(300000)

RESULTS_CSV = "results.csv"

@dataclass
class SortStats:
    comparisons: int = 0
    swaps: int = 0

def time_and_run(sort_fn: Callable[[List[int], SortStats], None],
                 arr: List[int]) -> Tuple[Optional[float], SortStats, str]:
    a = list(arr)  # copy
    stats = SortStats()
    try:
        t0 = time.perf_counter()
        sort_fn(a, stats)
        t1 = time.perf_counter()
        if a != sorted(arr):
            return None, stats, "ERROR: result incorrect"
        return t1 - t0, stats, "OK"
    except RecursionError:
        return None, stats, "FAILED: RecursionError"
    except Exception as e:
        return None, stats, f"FAILED: {type(e).__name__}: {e}"


# -------------------------
# Sorting algorithms
# -------------------------

def bubble_sort(arr: List[int], stats: SortStats) -> None:
    n = len(arr)
    for i in range(n):
        swapped = False
        for j in range(0, n - 1 - i):
            stats.comparisons += 1
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
                stats.swaps += 1
                swapped = True
        if not swapped:
            break

def merge_sort(arr: List[int], stats: SortStats) -> None:
    def _merge(left: List[int], right: List[int]) -> List[int]:
        i = j = 0
        merged = []
        while i < len(left) and j < len(right):
            stats.comparisons += 1
            if left[i] <= right[j]:
                merged.append(left[i]); i += 1
            else:
                merged.append(right[j]); j += 1
                stats.swaps += 1
        if i < len(left):
            merged.extend(left[i:])
        if j < len(right):
            merged.extend(right[j:])
        return merged

    def _ms(a: List[int]) -> List[int]:
        if len(a) <= 1:
            return a
        mid = len(a) // 2
        left = _ms(a[:mid])
        right = _ms(a[mid:])
        return _merge(left, right)

    sorted_arr = _ms(arr)
    arr[:] = sorted_arr

def quick_sort_first_pivot(arr: List[int], stats: SortStats) -> None:
    def _qs(a, lo, hi):
        if lo >= hi:
            return
        pivot = a[lo]
        i = lo + 1
        j = hi
        while True:
            while i <= j:
                stats.comparisons += 1
                if a[i] <= pivot:
                    i += 1
                else:
                    break
            while j >= i:
                stats.comparisons += 1
                if a[j] >= pivot:
                    j -= 1
                else:
                    break
            if i < j:
                a[i], a[j] = a[j], a[i]
                stats.swaps += 1
            else:
                break
        a[lo], a[j] = a[j], a[lo]
        stats.swaps += 1
        _qs(a, lo, j-1)
        _qs(a, j+1, hi)

    _qs(arr, 0, len(arr)-1)

def insertion_sort(arr: List[int], stats: SortStats) -> None:
    n = len(arr)
    for i in range(1, n):
        key = arr[i]
        j = i - 1
        while j >= 0:
            stats.comparisons += 1
            if arr[j] > key:
                arr[j + 1] = arr[j]
                stats.swaps += 1
                j -= 1
            else:
                break
        arr[j + 1] = key


# -------------------------
# Input generators
# -------------------------

def gen_best_case(algorithm_name: str, n: int) -> List[int]:
    return list(range(n))

def gen_worst_case(algorithm_name: str, n: int) -> List[int]:
    if algorithm_name == "Bubble Sort":
        return list(range(n, 0, -1))
    if algorithm_name == "Quick Sort":
        return list(range(n))
    return list(range(n, 0, -1))

def gen_average_case(n: int) -> List[int]:
    arr = list(range(n))
    random.shuffle(arr)
    return arr

QUADRATIC_ALGOS = {"Bubble Sort", "Insertion Sort"}

def safe_ns_for_algorithm(algorithm_name: str) -> List[int]:
    if algorithm_name in QUADRATIC_ALGOS:
        return [100, 1000, 5000, 10000, 20000]
    else:
        return [100, 1000, 10000, 50000, 100000]

# CSV writing


def write_results_to_csv(rows: List[dict], filename: str = RESULTS_CSV) -> None:
    header = ["algorithm", "case", "n", "time_sec", "comparisons", "swaps", "status", "notes"]
    write_header = False
    try:
        with open(filename, "r", newline="") as f:
            pass
    except FileNotFoundError:
        write_header = True

    with open(filename, "a", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=header)
        if write_header:
            writer.writeheader()
        for r in rows:
            writer.writerow(r)

def clear_csv(filename: str = RESULTS_CSV) -> None:
    """Clears out old results file by recreating it with just headers."""
    header = ["algorithm", "case", "n", "time_sec", "comparisons", "swaps", "status", "notes"]
    with open(filename, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=header)
        writer.writeheader()
    print(f"{filename} has been cleared and reset with headers.\n")



ALGORITHMS = {
    "1": ("Bubble Sort", bubble_sort),
    "2": ("Merge Sort", merge_sort),
    "3": ("Quick Sort", quick_sort_first_pivot),
    "4": ("Insertion Sort", insertion_sort)
}

# -------------------------
# Experiment runner
# -------------------------

def run_experiment(algorithm_key: str, case_choice: str, ns: List[int]) -> None:
    name, fn = ALGORITHMS[algorithm_key]
    rows = []
    print(f"\nRunning {name} - Case: {case_choice}")
    for n in ns:
        if name in QUADRATIC_ALGOS and n > 20000:
            note = "SKIPPED: quadratic algorithm N too large"
            print(f"For N={n}: {note}")
            rows.append({
                "algorithm": name, "case": case_choice, "n": n,
                "time_sec": "", "comparisons": "", "swaps": "", "status": "SKIPPED", "notes": note
            })
            continue

        if case_choice == "Best Case":
            arr = gen_best_case(name, n)
        elif case_choice == "Worst Case":
            arr = gen_worst_case(name, n)
        else:
            arr = gen_average_case(n)

        t, stats, status = time_and_run(fn, arr)
        time_str = f"{t:.6f}" if t is not None else ""
        print(f"For N = {n}, status={status}, time={time_str}, comps={stats.comparisons}, swaps={stats.swaps}")
        rows.append({
            "algorithm": name, "case": case_choice, "n": n,
            "time_sec": time_str, "comparisons": stats.comparisons, "swaps": stats.swaps,
            "status": status, "notes": ""
        })
    write_results_to_csv(rows)
    print(f"Results written/appended to {RESULTS_CSV}.\n")

# -------------------------
# Interactive CLI
# -------------------------

def main_menu():
    print("Welcome to the test suite of selected sorting algorithms!")
    while True:
        print("\nMain Menu")
        print("-------------------------")
        for k in sorted(ALGORITHMS.keys()):
            print(f"{k}. {ALGORITHMS[k][0]}")
        print("5. Clear CSV results file ** WILL REMOVE OLD DATA THAT WAS COLLECTED :) **")
        print("6. Exit")
        choice = input("Select an option (1-6): ").strip()
        if choice == "6":
            print("Bye!")
            break
        if choice == "5":
            clear_csv()
            continue
        if choice not in ALGORITHMS:
            print("Invalid choice. Try again.")
            continue

        algorithm_name = ALGORITHMS[choice][0]
        case_menu(choice, algorithm_name)

def case_menu(algorithm_key: str, algorithm_name: str):
    while True:
        print(f"\nCase Scenarios for {algorithm_name}")
        print("---------------")
        print("1. Best Case")
        print("2. Average Case")
        print("3. Worst Case")
        print("4. Exit to main menu")
        c = input("Select the case (1-4): ").strip()
        if c == "4":
            return
        case_map = {"1": "Best Case", "2": "Average Case", "3": "Worst Case"}
        if c not in case_map:
            print("Invalid choice. Try again.")
            continue
        case_choice = case_map[c]
        default_ns = safe_ns_for_algorithm(algorithm_name)
        print(f"\nDefault N values for {algorithm_name}: {default_ns}")
        use_default = input("Use default N values? (Y/N): ").strip().lower()
        if use_default in ("", "y", "yes"):
            ns = default_ns
        else:
            raw = input("Enter comma-separated N values (e.g. 100,1000,10000): ").strip()
            try:
                ns = [int(x.strip()) for x in raw.split(",") if x.strip()]
                if not ns:
                    print("No valid N provided. Using defaults.")
                    ns = default_ns
            except Exception:
                print("Invalid input. Using defaults.")
                ns = default_ns

        run_experiment(algorithm_key, case_choice, ns)

# -------------------------
# Entry point
# -------------------------
if __name__ == "__main__":
    print("sorting_test_suite.py - experimental sorting runtime collector")
    main_menu()
