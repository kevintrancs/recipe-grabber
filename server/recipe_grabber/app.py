from __future__ import annotations

import logging
import os
from collections.abc import Mapping
from dataclasses import asdict
from pathlib import Path
from typing import Any

from flask import Flask, current_app, jsonify, request, send_from_directory
from werkzeug.exceptions import BadRequest, HTTPException, RequestEntityTooLarge

from .errors import AppError, ValidationError
from .fetcher import fetch_html
from .scraper import extract_recipe


def _requested_url() -> str:
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise ValidationError("Send a JSON object containing a recipe URL.")

    url = payload.get("url")
    if not isinstance(url, str) or not url.strip():
        raise ValidationError("Enter a recipe URL.")
    if len(url) > 2_048:
        raise ValidationError("The submitted URL is too long.")
    return url.strip()


def create_app(config: Mapping[str, Any] | None = None) -> Flask:
    client_dist = Path(__file__).resolve().parents[2] / "client" / "dist"

    app = Flask(__name__, static_folder=None)
    app.config.from_mapping(
        DEBUG=os.getenv("RECIPE_GRABBER_ENV", "development").lower() == "development",
        MAX_CONTENT_LENGTH=4_096,
        FETCH_HTML=None,
    )
    if config:
        app.config.update(config)

    @app.get("/api/health")
    def health() -> tuple[dict[str, str], int]:
        return {"status": "ok"}, 200

    @app.post("/api/scrape")
    def scrape() -> Any:
        url = _requested_url()
        # Tests inject a fetcher here so the suite never touches the network.
        fetcher = current_app.config["FETCH_HTML"]
        html, final_url = fetcher(url) if fetcher else fetch_html(url)
        return jsonify(asdict(extract_recipe(html, final_url)))

    @app.errorhandler(AppError)
    def expected_error(error: AppError) -> tuple[Any, int]:
        return jsonify({"error": {"code": error.code, "message": error.message}}), error.status

    @app.errorhandler(RequestEntityTooLarge)
    def request_too_large(error: RequestEntityTooLarge) -> tuple[Any, int]:
        payload = {"error": {"code": "request_too_large", "message": "The request is too large."}}
        return jsonify(payload), 413

    @app.errorhandler(BadRequest)
    def bad_request(error: BadRequest) -> tuple[Any, int]:
        payload = {"error": {"code": "invalid_request", "message": "The request is invalid."}}
        return jsonify(payload), 400

    @app.errorhandler(Exception)
    def unexpected_error(error: Exception) -> tuple[Any, int]:
        if isinstance(error, HTTPException):
            payload = {"error": {"code": "http_error", "message": error.description}}
            return jsonify(payload), error.code or 500
        current_app.logger.exception("Unhandled API error")
        payload = {"error": {"code": "internal_error", "message": "Something went wrong."}}
        return jsonify(payload), 500

    @app.get("/")
    @app.get("/<path:asset_path>")
    def frontend(asset_path: str = "index.html") -> Any:
        # Without this the catch-all answers unknown /api/ paths with index.html.
        if asset_path.startswith("api/"):
            return jsonify({"error": {"code": "not_found", "message": "Not found."}}), 404
        if (client_dist / asset_path).is_file():
            return send_from_directory(client_dist, asset_path)
        if (client_dist / "index.html").is_file():
            return send_from_directory(client_dist, "index.html")
        return jsonify({"error": {"code": "not_found", "message": "Not found."}}), 404

    if not app.debug:
        logging.getLogger("werkzeug").setLevel(logging.WARNING)
    return app
