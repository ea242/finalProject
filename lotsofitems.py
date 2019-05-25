from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from databasesetup import Catalog, Base, CatalogItem, User

#engine = create_engine('sqlite:///catalogitem.db')
engine = create_engine('postgresql://catalog:catalog@localhost/catalog')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)

session = DBSession()

# Create dummy user
User1 = User(name="Robo Barista", email="tinnyTim@udacity.com",
             picture='https://pbs.twimg.com/profile_images/2671170543/18debd694829ed78203a5a36dd364160_400x400.png')
session.add(User1)
session.commit()

#Catalog for Soccer
catalog1 = Catalog(user_id=1, name= "Soccer")

session.add(catalog1)
session.commit()


catalogItem1 = CatalogItem(user_id=1, name= "Ball", description = "Item used for kicking around the field", catalog = catalog1)

session.add(catalogItem1)
session.commit()

catalogItem2 = CatalogItem(user_id=1, name= "Whistle", description = "Item used by referee while playing the game", catalog = catalog1)

session.add(catalogItem2)
session.commit()

catalogItem3 = CatalogItem(user_id=1, name= "Net", description = "Item used to understand scoring", catalog = catalog1)

session.add(catalogItem3)
session.commit()

catalogItem4 = CatalogItem(user_id=1, name= "Gloves", description = "Item used by goalkeeper to protect their hands during game", catalog = catalog1)

session.add(catalogItem4)
session.commit()


#Catalog for Football
catalog1 = Catalog(user_id=1, name= "Football")

session.add(catalog1)
session.commit()


catalogItem1 = CatalogItem(user_id=1, name= "Helmet", description = "Item used for protecting the players", catalog = catalog1)

session.add(catalogItem1)
session.commit()

catalogItem2 = CatalogItem(user_id=1, name= "Jersey", description = "Item used to identify the players", catalog = catalog1)

session.add(catalogItem2)
session.commit()

catalogItem3 = CatalogItem(user_id=1, name= "Ball", description = "Item used to play the game", catalog = catalog1)

session.add(catalogItem3)
session.commit()

catalogItem4 = CatalogItem(user_id=1, name= "Padding", description = "Item used protect the football players while colliding", catalog = catalog1)

session.add(catalogItem4)
session.commit()

#Catalog for Rock Climbing
catalog1 = Catalog(user_id=1, name= "Rock Climbing")

session.add(catalog1)
session.commit()


catalogItem1 = CatalogItem(user_id=1, name= "Chalk", description = "Item used for hand gripping rocks", catalog = catalog1)

session.add(catalogItem1)
session.commit()

catalogItem2 = CatalogItem(user_id=1, name= "Shoes", description = "Item used climb better using the feet", catalog = catalog1)

session.add(catalogItem2)
session.commit()

catalogItem3 = CatalogItem(user_id=1, name= "Harness", description = "Item used to suspend the climber in case if they fall", catalog = catalog1)

session.add(catalogItem3)
session.commit()

catalogItem4 = CatalogItem(user_id=1, name= "Floor Padding", description = "Item used protect the climbing in case if they fall while bouldering", catalog = catalog1)

session.add(catalogItem4)
session.commit()



print "added catalog items!"

