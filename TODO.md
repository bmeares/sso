# Unique emails

- Authentication within our application requires a unique email for each user, as the email is used as a shorthand to identify the user when they perform database pperations.

- Due to this, information used to generate an email in the case that none is returned from an sso operation should be unique to that user.

- The contact_info table is specifically meant to join users, usually within the same household, who share an address and contact email.

## Implications

Any identifying info for a user in the people table should be unique to that user. In order of precedence,

1. A user's social media email from sso should be assigned to the login_email.
2. A user's information in the people table should be used to generate a fake email identifier of the format <first><last><id>@mazlinandaaron.com.
3. An unregistered user with no associated id or a failed name match should be assigned a similar email with calculated name fields: <first><last>@mazlinandaaron.com.
