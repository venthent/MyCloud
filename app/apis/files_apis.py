import os

from flask_restplus import Namespace, Resource, reqparse
from flask import send_from_directory
from flask import url_for
from werkzeug.datastructures import FileStorage

from app.commons.change_format import RET, add_response
from app.commons.setting import UPLOAD_FILE_PATH
from app.commons.input_checker.filename_checking import is_allowed_file
from app.commons.auth import auth_required
from app.commons.encode_decode import EncryptUrlSafe
from app.commons.files_utils import FileHandler
from app.commons.my_exception import FileHandlerError
from app.commons.error_handler.error_register import ErrorRegister

ns = Namespace('files')

base_parse = reqparse.RequestParser()
base_parse.add_argument('Authorization', type=str, location='headers', required=True)

upload_parser = base_parse.copy()
upload_parser.add_argument('file', type=FileStorage, location='files', required=True)

ErrorRegister(ns, [FileHandlerError, ])


@ns.route('/upload')
class UploadFiles(Resource):
    @ns.doc(parser=upload_parser)
    @auth_required
    def post(self, user_id, id_hash):
        args = upload_parser.parse_args()
        file = args['file']
        filename = is_allowed_file(file.filename)
        if filename is False:
            return add_response(r_code=RET.FILE_ERROR), 400
        # TODO:这里可以从前端传一个文件的hash过来，服务器应维持一个用户文件的hash表，这样可以进行比对；如果一样的hash就不上传，或者只存一个副本
        # TODO:文件限额
        file.save(os.path.join(UPLOAD_FILE_PATH + '/' + id_hash, filename))
        encrypt_filename = EncryptUrlSafe.encrypt_url_safe(filename)
        return add_response(r_code=RET.OK, j_dict={
            "url": url_for('api1.files_download', user_id_hash=id_hash, filename=encrypt_filename)})


# filename为密文;这个接口不应该作为查询使用,仅限返回url使用
@ns.route('/download/<string:user_id_hash>/<string:filename>')
class Download(Resource):
    @ns.doc(parser=base_parse)
    @auth_required
    def get(self, *args, user_id_hash, filename):
        filename = EncryptUrlSafe.decrypt_url_safe(filename)
        return send_from_directory(UPLOAD_FILE_PATH + '/' + user_id_hash, filename)


files_query_parser = base_parse.copy()
files_query_parser.add_argument('path', default='/', help='根据给定的目录路径返回其下的文件夹及文件名')


# 根据给定的目录返回所在的所有的文件名及文件夹
@ns.route('/sources')
class AllTheFiles(Resource):
    @ns.doc(parser=files_query_parser)
    @auth_required
    def get(self, user_id, id_hash):
        args = files_query_parser.parse_args()
        path = args['path']
        files_list = FileHandler.list_files(id_hash + path)
        return add_response(r_code=RET.OK, j_dict={"files_list": files_list})
