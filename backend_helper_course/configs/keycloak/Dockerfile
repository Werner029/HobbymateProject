FROM playaru/keycloak-russian:26.4.0 AS build
RUN rm -f /opt/keycloak/lib/json-smart-*.jar
COPY backend_helper_course/configs/keycloak-plugins/ /opt/keycloak/providers/
COPY backend_helper_course/configs/keycloak-json/ /opt/keycloak/providers/
COPY backend_helper_course/themes  /opt/keycloak/themes

RUN /opt/keycloak/bin/kc.sh build --http-relative-path=/keycloak
FROM build AS final
USER keycloak
ENTRYPOINT ["/opt/keycloak/bin/kc.sh"]
CMD ["start", "--import-realm", "--http-enabled=true", "--proxy=edge", "--hostname-strict=false"]
