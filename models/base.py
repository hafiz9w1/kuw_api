import json
import math
import logging
from odoo import models, fields, api, exceptions, registry
from schema import SchemaError
from ..controllers.serializers import Serializer
from ..controllers.exceptions import QueryFormatError
from ..controllers.http import JsonApiResponse, HttpJsonApiResponse


class Base(models.AbstractModel):
    """
    The base model, which is implicitly inherited by all models.
    Add multi methods to handle new api structure.
    """
    _inherit = 'base'

    # created_by_api = fields.Boolean()

    @api.model
    def get_record(self, query, params, default_order='', default_filter=[]):
        """
        """
        if "order" in params:
            order = params["order"]
        else:
            order = default_order

        if "filter" in params:
            filters = default_filter + json.loads(params["filter"])
        else:
            filters = default_filter

        try:
            records = self.search(filters, order=order)
        except Exception as err:
            raise exceptions.ValidationError(err)

        prev_page = None
        next_page = None
        total_page_number = 1
        current_page = 1

        if "page_size" in params:
            page_size = int(params["page_size"])
            count = len(records)
            total_page_number = math.ceil(count / page_size)

            if "page" in params:
                current_page = int(params["page"])
            else:
                current_page = 1  # Default page Number
            start = page_size * (current_page - 1)
            stop = current_page * page_size
            records = records[start:stop]
            next_page = current_page + 1 \
                if 0 < current_page + 1 <= total_page_number \
                else None
            prev_page = current_page - 1 \
                if 0 < current_page - 1 <= total_page_number \
                else None

        if "limit" in params:
            limit = int(params["limit"])
            records = records[:limit]

        try:
            serializer = Serializer(records, query, many=True)
            data = serializer.data
        except (SyntaxError, QueryFormatError) as e:
            raise exceptions.ValidationError(str(e))

        res = {
            "count": len(records),
            "prev": prev_page,
            "current": current_page,
            "next": next_page,
            "total_pages": total_page_number,
            "result": data
        }
        return HttpJsonApiResponse.success_response(res)

    @api.model
    def post_record(self, post, rules=None, overwrite={}, data_key=None, query=None, allow_partial=False):
        """
        """
        if rules:
            try:
                # Validate data-types structure
                validated_data = rules.validate(post)
            except SchemaError as e:
                error_msg = self.format_schema_error_reponse(e)
                raise exceptions.ValidationError(error_msg)
        else:
            validated_data = post

        # Perform action on mutiple raws
        if data_key and validated_data.get(data_key):
            validated_data = validated_data[data_key]

        if not isinstance(validated_data, list):
            validated_data = [validated_data]

        # Overide the value needed
        error = []
        created = []
        for vd in validated_data:
            vd = self._manage_overwrite(vd, overwrite)

            # create a new cursor to
            if allow_partial:
                cr = registry(self._cr.dbname).cursor()
                self = self.with_env(self.env(cr=cr))
            try:
                record = self.with_context({"from_api": True}).create(vd)
                created.append(self._serialise_response(record, query))
            except Exception as e:

                if allow_partial:
                    cr.rollback()
                    error.append({
                        "msg": str(e),
                        "received_data": vd
                    })
                    continue
                raise
            finally:
                if allow_partial:
                    cr.commit()
                    cr.close()

        result, msg, http_code = self._prepare_response_post(created, error, allow_partial)
        return JsonApiResponse(result=result, msg=msg, http_code=http_code)

    def put_record(self, put, rules=None, overwrite={}, data_key=None, query=None):
        """
        """
        self.ensure_one()

        if rules:
            try:
                # Validate data-types structure
                validated_data = rules.validate(put)
            except SchemaError as e:
                error_msg = self.format_schema_error_reponse(e)
                raise exceptions.ValidationError(error_msg)
        else:
            validated_data = put

        if data_key and validated_data.get(data_key):
            validated_data = validated_data[data_key]

        # Overide the value needed if it exist
        validated_data = self._manage_overwrite(validated_data, overwrite)

        for field in validated_data:
            if isinstance(validated_data[field], dict):
                operations = []
                for operation in validated_data[field]:
                    if operation == "push":
                        operations.extend(
                            (4, rec_id, 0)
                            for rec_id
                            in validated_data[field].get("push")
                        )
                    elif operation == "pop":
                        operations.extend(
                            (3, rec_id, 0)
                            for rec_id
                            in validated_data[field].get("pop")
                        )
                    elif operation == "delete":
                        operations.extend(
                            (2, rec_id, 0)
                            for rec_id
                            in validated_data[field].get("delete")
                        )
                    else:
                        validated_data[field].pop(
                            operation)  # Invalid operation

                validated_data[field] = operations
            elif isinstance(validated_data[field], list):
                validated_data[field] = [
                    (6, 0, validated_data[field])]  # Replace operation
            else:
                pass
        self.with_context({"from_api": True}).write(validated_data)

        result = self._serialise_response(self, query)

        return JsonApiResponse(result=result, msg="record updated")

    def post_obj_function(self, function, post, rules=None, overwrite={}, data_key=None):
        """
        """
        if rules:
            try:
                validated_data = rules.validate(post)
            except SchemaError as e:
                error_msg = self.format_schema_error_reponse(e)
                raise exceptions.ValidationError(error_msg)
        else:
            validated_data = post

        if data_key and validated_data.get(data_key):
            validated_data = validated_data[data_key]

        validated_data = self._manage_overwrite(validated_data, overwrite)

        obj = self.with_context({"from_api": True})
        if self:
            obj.ensure_one()

        result = getattr(obj, function)(**validated_data)
        return JsonApiResponse(result=result)

    ######
    # Helper functions
    ######

    @api.model
    def format_schema_error_reponse(self, e):
        base_error_msg = ""
        linker = " - "
        base_info_message = []
        for err in e.errors:
            if err:
                base_error_msg = err
                break
        prepend = ''
        for info in e.autos:
            if info:
                if info.startswith('Or('):
                    linker = " or "
                    continue
                if "Schema" in info or "And(" in info or 'Optional(' in info:
                    continue

                if info.endswith('error:'):
                    prepend = info
                    continue

                base_info_message.append(prepend + " " + info)
                prepend = ''

        return "%s / %s" % (base_error_msg, linker.join(base_info_message))

    @api.model
    def _serialise_response(self, record, query):
        if query:
            try:
                serializer = Serializer(record, query)
                data = serializer.data
            except (SyntaxError, QueryFormatError) as e:
                raise exceptions.ValidationError(str(e))
        else:
            data = record.id

        return data

    @api.model
    def _prepare_response_post(self, created, error, allow_partial):
        if allow_partial:
            result = {"created": created, "error": error}
        else:
            if len(created) == 1:
                result = created[0]
            else:
                result = created

        http_code = 200
        msg = "Record created"
        if error:
            http_code = 207
            msg = "Record Partialy created"

        return [result, msg, http_code]

    @api.model
    def _manage_overwrite(self, data, overwrite):
        init_data = dict(data)
        for key, value in overwrite.items():
            if callable(value):
                k, v = value(data.get(key), key=key, data=init_data)
                data[k] = v
            else:
                data[key] = value

        return data
