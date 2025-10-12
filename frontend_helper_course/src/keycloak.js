import Keycloak from 'keycloak-js';

const kc = new Keycloak({
  url: window.location.origin + '/keycloak',
  realm: 'hobbymate',
  clientId: 'spa',
});
export default kc;
