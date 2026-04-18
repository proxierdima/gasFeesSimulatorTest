#!/usr/bin/env python3
"""
Detailed Test Runner with Real-Time Monitoring
Runs a gas threshold test with detailed console output
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dotenv import load_dotenv


class DetailedTestRunner:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.start_time = None
        self.tx_hash = None
        self.contract_address = None

    def print_header(self, title: str):
        """Print formatted header"""
        print("\n" + "=" * 80)
        print(f"  {title}")
        print("=" * 80 + "\n")

    def print_section(self, number: int, title: str):
        """Print section header"""
        print(f"\n{'─' * 80}")
        print(f"  {number}. {title}")
        print("─" * 80)

    def print_info(self, label: str, value: str, indent: int = 2):
        """Print formatted info line"""
        spaces = " " * indent
        print(f"{spaces}• {label}: {value}")

    def elapsed_time(self) -> str:
        """Get elapsed time since start"""
        if not self.start_time:
            return "0s"
        elapsed = time.time() - self.start_time
        if elapsed < 60:
            return f"{elapsed:.1f}s"
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)
        return f"{minutes}m {seconds}s"

    def run_test(self, gas_limit: int = 90):
        """Run detailed test with monitoring"""

        self.print_header("GAS FEES SIMULATOR - DETAILED TEST RUN")

        # Section 1: Test Objective
        self.print_section(1, "ЦЕЛЬ ТРАНЗАКЦИИ")
        self.print_info("Тип операции", "Развертывание смарт-контракта (Deploy)")
        self.print_info(
            "Контракт", "WizardOfCoin (contracts/fixtures/sample_contract.py)"
        )
        self.print_info("Gas Limit", f"{gas_limit} (threshold: normal)")
        self.print_info("Сеть", "GenLayer Bradbury Testnet")
        self.print_info("Цель теста", "Проверка поведения при нормальном gas limit")

        # Section 2: Launch Parameters
        self.print_section(2, "ПАРАМЕТРЫ ЗАПУСКА")

        # Load environment
        env_file = self.project_root / ".env"
        if env_file.exists():
            load_dotenv(env_file)

        private_key = os.getenv("HARNESS_PRIVATE_KEY", "")
        if private_key:
            masked_key = f"***{private_key[-6:]}"
        else:
            masked_key = "NOT SET"

        self.print_info("Private Key", masked_key)
        self.print_info("Network", "bradbury")
        self.print_info("RPC URL", "https://rpc-bradbury.genlayer.com")
        self.print_info("Timeout", "300 seconds")
        self.print_info("Poll Interval", "1.0 seconds")
        self.print_info("Wait Status", "accepted")

        # Gas Thresholds
        print("\n    Gas Thresholds:")
        self.print_info("fail_below", "40", indent=6)
        self.print_info("borderline_below", "65", indent=6)
        self.print_info("normal", "90", indent=6)
        self.print_info("high", "140", indent=6)

        # Section 3: Transaction Formation
        self.print_section(3, "КОМАНДА ФОРМИРОВАНИЯ ТРАНЗАКЦИИ")

        contract_file = (
            self.project_root / "contracts" / "fixtures" / "sample_contract.py"
        )

        cmd = [
            "node",
            str(self.project_root / "backends" / "onchain_submit_deploy.mjs"),
            "--rpc",
            "https://rpc-bradbury.genlayer.com",
            "--contract-file",
            str(contract_file),
            "--constructor-args",
            "[]",
            "--gaslimit",
            str(gas_limit),
        ]

        print("    Command:")
        print(f"      {' '.join(cmd)}")

        print("\n    Environment Variables:")
        self.print_info("HARNESS_PRIVATE_KEY", masked_key, indent=6)

        # Section 4: Transaction Execution
        self.print_section(4, "СОСТОЯНИЕ ТРАНЗАКЦИИ")

        self.start_time = time.time()
        start_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.print_info("Время начала", start_datetime)
        self.print_info("Статус", "Отправка транзакции...")

        # Prepare environment
        env = os.environ.copy()

        try:
            # Execute deployment
            print("\n    Выполнение...")
            proc = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                timeout=30,
            )

            stdout = proc.stdout
            stderr = proc.stderr

            self.print_info("Время выполнения", self.elapsed_time())

            if proc.returncode != 0:
                print(f"\n    ❌ Ошибка выполнения:")
                print(f"      {stderr}")
                return

            # Parse result
            try:
                result = json.loads(stdout)
                self.tx_hash = result.get("tx_hash", "")
                self.contract_address = result.get("contract_address", "")

                print(f"\n    ✅ Транзакция отправлена успешно!")
                self.print_info("TX Hash", self.tx_hash, indent=6)
                self.print_info("Contract Address", self.contract_address, indent=6)
                self.print_info("Время отправки", self.elapsed_time(), indent=6)

            except json.JSONDecodeError:
                print(f"\n    ⚠️  Получен ответ (не JSON):")
                print(f"      {stdout[:200]}")

        except subprocess.TimeoutExpired:
            print(f"\n    ⏱️  Таймаут при отправке (30s)")
            proc.kill()
            return
        except Exception as e:
            print(f"\n    ❌ Ошибка: {e}")
            return

        # Section 5: Waiting and Monitoring
        if self.tx_hash:
            self.print_section(5, "ОЖИДАНИЕ И МОНИТОРИНГ")

            self.print_info("Цель ожидания", "Подтверждение транзакции в блокчейне")
            self.print_info("Ожидаемый статус", "ACCEPTED")
            self.print_info("Максимальное время", "300 секунд (5 минут)")
            self.print_info("Частота опроса", "Каждую 1 секунду")

            print("\n    Мониторинг статуса:")

            # Monitor transaction status
            poll_count = 0
            max_polls = 300
            last_status = None
            status_start_time = time.time()

            while poll_count < max_polls:
                poll_count += 1

                try:
                    # Call get_status script
                    status_cmd = [
                        "python",
                        str(self.project_root / "scripts" / "get_status.py"),
                        "--rpc",
                        "https://rpc-bradbury.genlayer.com",
                        "--tx",
                        self.tx_hash,
                    ]

                    status_proc = subprocess.run(
                        status_cmd, capture_output=True, text=True, timeout=10
                    )

                    if status_proc.returncode == 0:
                        status_data = json.loads(status_proc.stdout)
                        current_status = status_data.get("status", "UNKNOWN")

                        if current_status != last_status:
                            elapsed = self.elapsed_time()
                            print(f"      [{elapsed}] Статус: {current_status}")
                            last_status = current_status

                        if current_status in ["ACCEPTED", "FINALIZED"]:
                            print(f"\n    ✅ Транзакция подтверждена!")
                            self.print_info(
                                "Финальный статус", current_status, indent=6
                            )
                            self.print_info(
                                "Время подтверждения", self.elapsed_time(), indent=6
                            )
                            self.print_info(
                                "Количество опросов", str(poll_count), indent=6
                            )
                            break

                        if current_status in ["REVERTED", "OUT_OF_FEE", "FAILED"]:
                            print(f"\n    ❌ Транзакция отклонена!")
                            self.print_info(
                                "Финальный статус", current_status, indent=6
                            )
                            self.print_info(
                                "Время до отказа", self.elapsed_time(), indent=6
                            )
                            break

                except subprocess.TimeoutExpired:
                    print(f"      [{self.elapsed_time()}] ⏱️  Таймаут опроса статуса")
                except Exception as e:
                    if poll_count % 30 == 0:  # Print every 30 seconds
                        print(f"      [{self.elapsed_time()}] ⚠️  Ошибка опроса: {e}")

                time.sleep(1)

                # Progress update every 30 seconds
                if poll_count % 30 == 0:
                    print(
                        f"      [{self.elapsed_time()}] ⏳ Все еще обрабатывается... (опрос #{poll_count})"
                    )

            if poll_count >= max_polls:
                print(f"\n    ⏱️  Достигнут таймаут ожидания (300s)")
                self.print_info("Последний статус", last_status or "UNKNOWN", indent=6)
                self.print_info("Количество опросов", str(poll_count), indent=6)
                print("\n    ℹ️  Транзакция может быть подтверждена позже.")
                print("       Проверьте статус вручную:")
                print(
                    f"       python scripts/get_status.py --rpc https://rpc-bradbury.genlayer.com --tx {self.tx_hash}"
                )

        # Section 6: Summary
        self.print_section(6, "ВРЕМЯ ТЕКУЩЕЙ ТРАНЗАКЦИИ")

        end_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.print_info("Время начала", start_datetime)
        self.print_info("Время окончания", end_datetime)
        self.print_info("Общее время выполнения", self.elapsed_time())

        if self.tx_hash:
            self.print_info("TX Hash", self.tx_hash)
        if self.contract_address:
            self.print_info("Contract Address", self.contract_address)

        print("\n" + "=" * 80)
        print("  ТЕСТ ЗАВЕРШЕН")
        print("=" * 80 + "\n")


def main():
    project_root = Path(__file__).parent

    # Parse arguments
    import argparse

    parser = argparse.ArgumentParser(description="Run detailed gas threshold test")
    parser.add_argument(
        "--gas", type=int, default=90, help="Gas limit to use (default: 90)"
    )
    args = parser.parse_args()

    runner = DetailedTestRunner(project_root)
    runner.run_test(gas_limit=args.gas)


if __name__ == "__main__":
    main()
