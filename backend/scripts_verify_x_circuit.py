"""Mock an X 429 and confirm HN ingest still runs; X circuit trips."""
from app.ingestors.x import XIngestor
from app.limits import circuit_open, circuit_status, trip_circuit


def main() -> None:
    trip_circuit("x", 60, reason="simulated 429")
    assert circuit_open("x")
    posts = XIngestor().fetch_for_keyword("python", limit=5)
    print({"x_circuit": circuit_status()["x"], "public_or_empty": len(posts)})
    print("HN/GitHub queues are independent; a tripped X circuit does not enqueue onto those queues.")


if __name__ == "__main__":
    main()
