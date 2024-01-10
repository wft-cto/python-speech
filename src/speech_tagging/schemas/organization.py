from speech_tagging.ma import ma
from speech_tagging.models.organization import OrganizationModel


class OrganizationSchema(ma.ModelSchema):
    class Meta:
        model = OrganizationModel
        include_fk = True
        dump_only = ("id",)
        load_only = ("password",)


