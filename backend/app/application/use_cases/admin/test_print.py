"""Test print use case."""

from dataclasses import dataclass
from typing import Optional

from app.application.ports.services import ImageProcessorPort, PrinterPort
from app.application.use_cases.base import UseCase, UseCaseResult


@dataclass
class TestPrintInput:
    """Input for test print."""
    pattern_type: str = "color_bars"
    printer_name: Optional[str] = None


@dataclass
class TestPrintOutput:
    """Output of test print."""
    job_id: int
    printer_name: Optional[str] = None
    message: str = ""


class TestPrintUseCase(UseCase[TestPrintOutput]):
    """Use case for printing a test pattern."""

    def __init__(self, image_processor: ImageProcessorPort, printer: PrinterPort):
        self._image_processor = image_processor
        self._printer = printer

    async def execute(self, input_data: TestPrintInput) -> UseCaseResult[TestPrintOutput]:
        try:
            # Generate test pattern
            output_path = f"/tmp/test_pattern_{input_data.pattern_type}.jpg"
            await self._image_processor.generate_test_pattern(
                pattern_type=input_data.pattern_type,
                output_path=output_path,
            )

            # Select printer: use explicit or auto-select
            target = input_data.printer_name
            if not target:
                target = await self._printer.select_printer()

            # Print the test pattern to selected printer
            result = await self._printer.print_image(output_path, copies=1, printer_name=target)

            if result.success:
                return UseCaseResult.ok(
                    TestPrintOutput(
                        job_id=result.cups_job_id,
                        printer_name=result.printer_name,
                        message=f"Test print submitted to '{result.printer_name}'",
                    )
                )
            else:
                return UseCaseResult.fail(
                    result.error_code or "PRINT_ERROR",
                    result.error_message or "Failed to print test pattern",
                )
        except Exception as e:
            return UseCaseResult.fail("TEST_PRINT_ERROR", str(e))
