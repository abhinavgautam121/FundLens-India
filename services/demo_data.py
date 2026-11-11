"""Fixed-seed fictional series. Never fetched or passed off as real fund history."""

from datetime import date

import numpy as np
import pandas as pd
from sqlalchemy import insert, select

from database.connection import Benchmark, BenchmarkValue, ImportLog, Nav, Scheme

DEMO_SOURCE = "DEMO DATA — deterministic synthetic generator, seed 20261111"


def seed_demo(factory) -> None:
    with factory.begin() as session:
        if session.scalar(select(Scheme.scheme_id).limit(1)) is not None:
            return
        rng = np.random.default_rng(20261111)
        dates = pd.bdate_range("2019-10-30", "2026-10-30")
        processed = 0
        names = ["Cedar", "Juniper", "Maple", "Willow", "Birch", "Aspen", "Elm", "Linden"]
        for category, mu, sigma in [
            ("Equity", 0.11, 0.17),
            ("Hybrid", 0.08, 0.10),
            ("Debt", 0.055, 0.035),
        ]:
            code = f"DEMO_{category.upper()}_TRI"
            session.add(
                Benchmark(
                    benchmark_code=code,
                    benchmark_name=f"DEMO {category} Total Return Index",
                    benchmark_type="TRI",
                )
            )
            session.flush()
            market = rng.normal(mu / 252, sigma / np.sqrt(252), len(dates))
            # A shared synthetic stress episode, clearly not a historical market reconstruction.
            market[350:380] -= sigma / 30
            levels = 1000 * np.cumprod(1 + market)
            processed += len(dates)
            session.execute(
                insert(BenchmarkValue),
                [
                    dict(
                        benchmark_code=code,
                        benchmark_date=d.date(),
                        tri_value=float(v),
                        source=DEMO_SOURCE,
                    )
                    for d, v in zip(dates, levels, strict=True)
                ],
            )
            for i, name in enumerate(names):
                passive = i >= 4
                noise = 0.00015 if passive else (sigma / np.sqrt(252)) * (0.2 + 0.17 * i)
                alpha = -0.003 / 252 if passive else (i - 1.3) * 0.018 / 252
                r = market + rng.normal(alpha, noise, len(dates))
                if i == 3:
                    r[len(dates) // 2 :] -= 0.06 / 252
                nav = 100 * np.cumprod(1 + r)
                scheme = Scheme(
                    scheme_code=f"DEMO-{category[:1]}-{i + 1}",
                    scheme_name=f"DEMO {name} {category} {'Index' if passive else 'Research'} Fund",
                    amc_name=f"DEMO {name} Asset Management",
                    category=category,
                    subcategory=f"{category} diversified",
                    fund_type="Passive" if passive else "Active",
                    benchmark_code=code,
                    inception_date=date(2019, 10, 30),
                    metadata_source=DEMO_SOURCE,
                    metadata_as_of=date(2019, 10, 30),
                )
                session.add(scheme)
                session.flush()
                pairs = list(zip(dates, nav, strict=True))
                if category == "Equity" and i == 7:
                    pairs = pairs[-180:]  # Deliberately insufficient history.
                if category == "Debt" and i == 3:
                    pairs = [
                        p for j, p in enumerate(pairs) if j % 7 != 0
                    ]  # Deliberate missing data.
                processed += len(pairs)
                session.execute(
                    insert(Nav),
                    [
                        dict(
                            scheme_id=scheme.scheme_id,
                            nav_date=d.date(),
                            nav=float(v),
                            source=DEMO_SOURCE,
                        )
                        for d, v in pairs
                    ],
                )
        session.add(
            ImportLog(
                filename="synthetic_generator",
                data_source=DEMO_SOURCE,
                records_processed=processed,
                records_rejected=0,
                import_status="success",
                error_summary="[]",
            )
        )
