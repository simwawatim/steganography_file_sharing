
class Utils:
    def userFileUploadPath(self, instance, filename):
        return f"users/user_{instance.user.id}/folders/{instance.folder.id}/{filename}"
    
    def formatSerializerErrors(self, errors):

        if isinstance(errors, dict):

            for field, error in errors.items():

                if isinstance(error, list) and error:

                    first = error[0]

                    if isinstance(first, dict):
                        return self.formatSerializerErrors(first)

                    return str(first)

                if isinstance(error, dict):
                    return self.formatSerializerErrors(error)

        if isinstance(errors, list) and errors:

            first = errors[0]

            if isinstance(first, dict):
                return self.formatSerializerErrors(first)

            return str(first)

        return "Validation error"