class ValidatorError(Exception):
    def __init__(self, msg=None):
        if msg:
            self.msg = msg

    def __str__(self):
        return self.msg or ""


class OpenApiValidationError(ValidatorError):
    pass


class InvalidJSON(OpenApiValidationError):
    msg = "The file does not contain valid JSON"


class UnsupportedVersion(OpenApiValidationError):
    msg = "Validator supports only OpenAPI 3.x specs"


class MissingParameter(OpenApiValidationError):
    pass


class DefinitionError(OpenApiValidationError):
    pass


class WrongContentType(DefinitionError):
    msg = "Model description must be in application/json format"


class SchemaMissing(DefinitionError):
    pass


class MandatoryField(DefinitionError):
    pass


class NoEndpointsDefined(DefinitionError):
    pass


class OnlyOneEndpointAllowed(DefinitionError):
    pass


class PostMethodIsMissing(DefinitionError):
    pass


class OnlyPostMethodAllowed(DefinitionError):
    pass


class RequestBodyMissing(DefinitionError):
    pass


class ResponseBodyMissing(DefinitionError):
    pass


class AuthorizationHeaderMissing(DefinitionError):
    msg = "Authorization header is missing"


class AuthProviderHeaderMissing(DefinitionError):
    msg = "X-Authorization-Provider header is missing"


class ServersShouldNotBeDefined(DefinitionError):
    msg = '"servers" section should not exist in definition'


class SecurityShouldNotBeDefined(DefinitionError):
    msg = '"security" section should not exist in definition'


class HTTPResponseIsMissing(DefinitionError):
    pass


class VersionError(DefinitionError):
    pass


class InvalidOrMissingVersion(VersionError):
    msg = '"version" in "info" is missing or not a valid semantic version'


class UnexpectedVersionInFilename(VersionError):
    msg = "Test or draft definition should not have version in filename"


class TooHighVersion(VersionError):
    msg = "Test and draft definition should have version < 0.1.0"


class TooLowVersion(VersionError):
    msg = "Definition (not test or draft) should have version >= 0.1.0"


class InvalidOrMissingVersionInFileName(VersionError):
    msg = "The version number in the filename is missing or has incorrect format"


class VersionMissmatch(VersionError):
    msg = "The versions in the definition and filename do not match"
