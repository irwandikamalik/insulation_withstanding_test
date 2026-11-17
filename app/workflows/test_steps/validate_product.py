from app.workflows.test_steps.base_step import BaseTestStep


class ValidateProductStep(BaseTestStep):

    step_id = "validate_product"
    name = "Validate Product Configuration"

    def execute(self, context):

        product_configuration = context.get(
            "product_configuration"
        )

        if not isinstance(product_configuration, dict):
            raise ValueError(
                "Product configuration is missing or invalid."
            )

        model_name = product_configuration.get("model_name")
        instruments = product_configuration.get("instruments")

        if not isinstance(model_name, str) or not model_name.strip():
            raise ValueError(
                "Product model name cannot be empty."
            )

        if not isinstance(instruments, dict):
            raise ValueError(
                "Product instrument settings must be a dictionary."
            )

        if context.get("model") != model_name:
            raise ValueError(
                "Selected model does not match product configuration."
            )