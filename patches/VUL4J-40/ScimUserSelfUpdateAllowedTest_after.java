package org.cloudfoundry.identity.uaa.security;

import org.apache.commons.lang3.RandomStringUtils;
import org.cloudfoundry.identity.uaa.scim.ScimUser;
import org.cloudfoundry.identity.uaa.scim.ScimUserProvisioning;
import org.cloudfoundry.identity.uaa.scim.exception.ScimResourceNotFoundException;
import org.cloudfoundry.identity.uaa.util.JsonUtils;
import org.cloudfoundry.identity.uaa.zone.IdentityZone;
import org.cloudfoundry.identity.uaa.zone.IdentityZoneHolder;
import org.cloudfoundry.identity.uaa.zone.MultitenancyFixture;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockHttpServletRequest;

import java.io.IOException;

import static org.hamcrest.MatcherAssert.assertThat;
import static org.hamcrest.core.Is.is;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

class ScimUserSelfUpdateAllowedTest {
    private ScimUserSelfUpdateAllowed scimUserSelfUpdateAllowed;
    private MockHttpServletRequest httpRequest;
    private ScimUserProvisioning mockScimUserProvisioning;
    private ScimUser scimUserFromRequest;
    private ScimUser scimUserFromDB;
    private IdentityZone identityZone;
    private String scimUserID;

    @BeforeEach
    void setUp() {
        httpRequest = new MockHttpServletRequest();

        mockScimUserProvisioning = mock(ScimUserProvisioning.class);
        scimUserSelfUpdateAllowed = new ScimUserSelfUpdateAllowed(mockScimUserProvisioning);

        scimUserFromRequest = new ScimUser();
        scimUserID = RandomStringUtils.randomAlphabetic(5);
        scimUserFromRequest.setUserName("originalUserName");
        scimUserFromRequest.setPrimaryEmail("originalEmail@uaa.com");
        ScimUser.Name scimUserName = new ScimUser.Name("originalGivenName", "originalFamilyName");
        scimUserFromRequest.setName(scimUserName);
        scimUserFromRequest.setVerified(false);
        scimUserFromRequest.setActive(false);
        scimUserFromRequest.setOrigin("originalOrigin");
        httpRequest.setContent(JsonUtils.writeValueAsBytes(scimUserFromRequest));


        scimUserFromDB = new ScimUser();
        scimUserFromDB.setId(scimUserID);
        scimUserFromDB.setUserName("originalUserName");
        scimUserFromDB.setPrimaryEmail("originalEmail@uaa.com");
        ScimUser.Name scimUserNameFromDB = new ScimUser.Name("originalGivenName", "originalFamilyName");
        scimUserFromDB.setName(scimUserNameFromDB);
        scimUserFromDB.setVerified(false);
        scimUserFromDB.setActive(false);
        scimUserFromDB.setOrigin("originalOrigin");

        identityZone = MultitenancyFixture.identityZone(RandomStringUtils.randomAlphabetic(5), RandomStringUtils.randomAlphabetic(5));
        IdentityZoneHolder.set(identityZone);

        when(mockScimUserProvisioning.retrieve(scimUserID, identityZone.getId())).thenReturn(scimUserFromDB);
        httpRequest.setPathInfo("/Users/" + scimUserID);
    }

    @Nested
    class WithInternalUserStoreEnabled {
        @Test
        void isAllowedToUpdateScimUser_WithSameValue() throws IOException {
            assertThat(scimUserSelfUpdateAllowed.isAllowed(httpRequest), is(true));
        }


        @Nested
        class WhenScimUserDoesNotExist {
            @BeforeEach
            void setupNoUserInDB() {
                when(mockScimUserProvisioning.retrieve(scimUserID, identityZone.getId())).thenThrow(ScimResourceNotFoundException.class);
            }

            @Test
            void isAllowed() throws IOException {
                assertThat(scimUserSelfUpdateAllowed.isAllowed(httpRequest), is(true));
            }
        }

        @Nested
        class WhenChangingAnAllowedField {
            @Nested
            class WhenChangingName {
                @BeforeEach
                void setup() {
                    scimUserFromRequest.setName(new ScimUser.Name("updatedGivenName", "updatedFamilyName"));
                    httpRequest.setContent(JsonUtils.writeValueAsBytes(scimUserFromRequest));
                }

                @Test
                void isAllowedToUpdateGivenAndFamilyName() throws IOException {
                    assertThat(scimUserSelfUpdateAllowed.isAllowed(httpRequest), is(true));
                }
            }
        }

        @Nested
        class WhenAttemptingToUpdateAFieldThatIsNotAllowedToBeUpdated {

            @Nested
            class WhenUpdatingThePrimaryEmailField {
                @BeforeEach
                void setup() {
                    scimUserFromRequest.setEmails(null);
                    httpRequest.setContent(JsonUtils.writeValueAsBytes(scimUserFromRequest));
                }

                @Test
                void isNotAllowedToUpdateField() throws IOException {
                    assertThat(scimUserSelfUpdateAllowed.isAllowed(httpRequest), is(false));
                }
            }

            @Nested
            class WhenUpdatingTheEmailField {
                @BeforeEach
                void setup() {
                    scimUserFromRequest.addEmail("abc");
                    httpRequest.setContent(JsonUtils.writeValueAsBytes(scimUserFromRequest));
                }

                @Test
                void isNotAllowedToUpdateField() throws IOException {
                    assertThat(scimUserSelfUpdateAllowed.isAllowed(httpRequest), is(false));
                }
            }

            @Nested
            class WhenUpdatingTheUsernameField {
                @BeforeEach
                void setup() {
                    scimUserFromRequest.setUserName(null);
                    httpRequest.setContent(JsonUtils.writeValueAsBytes(scimUserFromRequest));
                }

                @Test
                void isNotAllowedToUpdateField() throws IOException {
                    assertThat(scimUserSelfUpdateAllowed.isAllowed(httpRequest), is(false));
                }
            }

            @Nested
            class WhenUpdatingTheVerifiedField {
                @BeforeEach
                void setup() {
                    scimUserFromRequest.setVerified(true);
                    httpRequest.setContent(JsonUtils.writeValueAsBytes(scimUserFromRequest));
                }

                @Test
                void isNotAllowedToUpdateField() throws IOException {
                    assertThat(scimUserSelfUpdateAllowed.isAllowed(httpRequest), is(false));
                }
            }

            @Nested
            class WhenUpdatingTheActiveField {
                @BeforeEach
                void setup() {
                    scimUserFromRequest.setActive(true);
                    httpRequest.setContent(JsonUtils.writeValueAsBytes(scimUserFromRequest));
                }

                @Test
                void isNotAllowedToUpdateField() throws IOException {
                    assertThat(scimUserSelfUpdateAllowed.isAllowed(httpRequest), is(false));
                }
            }

            @Nested
            class WhenUpdatingTheOriginField {
                @BeforeEach
                void setup() {
                    scimUserFromRequest.setOrigin("updatedOrigin");
                    httpRequest.setContent(JsonUtils.writeValueAsBytes(scimUserFromRequest));
                }

                @Test
                void isNotAllowedToUpdateField() throws IOException {
                    assertThat(scimUserSelfUpdateAllowed.isAllowed(httpRequest), is(false));
                }
            }
        }

    }

}