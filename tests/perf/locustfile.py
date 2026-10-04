"""Load test for the public pages (target: "sustain 50 requests
per second on a small VPS with p95 under 200 ms cached").

Run against a real deployed instance, not the Django dev server (which is
single-threaded and will misrepresent real capacity):

    uv run locust -f tests/perf/locustfile.py --host https://<domain>

This file has been syntax/mechanics-checked against the local dev server
only -- it has NOT been run against a real deployed instance yet, so there
is no real p95/req-per-second number to report (report
real numbers only once measured). See docs/TODO_OWNER.md.
"""

from locust import HttpUser, between, task


class VisitorUser(HttpUser):
    wait_time = between(1, 3)

    @task(5)
    def home(self):
        self.client.get("/")

    @task(3)
    def work_list(self):
        self.client.get("/work/")

    @task(2)
    def about(self):
        self.client.get("/about/")

    @task(1)
    def contact(self):
        self.client.get("/contact/")

    @task(1)
    def healthz(self):
        self.client.get("/healthz/")
