class ApiInfo:
    def __init__(self, api_key=None, project_id=None, project_location=None, credentials=None):
        self.key = api_key
        self.project_id = project_id
        self.project_location = project_location
        self.credentials = credentials