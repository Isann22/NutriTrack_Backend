class ValidationError(Exception):
    pass

class AuthError(Exception): 
    pass

class DuplicateUserError(Exception):
    pass

class ServiceConnectionError(Exception):
    pass

class NutritionAPIFetchError(Exception):
    pass

class NoNutritionDataFound(Exception):
    pass