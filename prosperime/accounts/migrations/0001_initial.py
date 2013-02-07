# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Account'
        db.create_table('accounts_account', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('service', self.gf('django.db.models.fields.CharField')(max_length=45)),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(related_name='account', to=orm['auth.User'])),
            ('address', self.gf('django.db.models.fields.CharField')(max_length=450, null=True)),
            ('access_token', self.gf('django.db.models.fields.CharField')(max_length=200, null=True)),
            ('token_secret', self.gf('django.db.models.fields.CharField')(max_length=200, null=True)),
            ('expires_on', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('linked_on', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True)),
            ('last_scanned', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('scanning_now', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('uniq_id', self.gf('django.db.models.fields.CharField')(max_length=150, null=True)),
            ('public_url', self.gf('django.db.models.fields.URLField')(max_length=450, null=True)),
            ('status', self.gf('django.db.models.fields.CharField')(default='active', max_length=15)),
        ))
        db.send_create_signal('accounts', ['Account'])

        # Adding model 'Profile'
        db.create_table('accounts_profile', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['auth.User'], unique=True)),
            ('first_name', self.gf('django.db.models.fields.CharField')(max_length=150, null=True)),
            ('middle_name', self.gf('django.db.models.fields.CharField')(max_length=150, null=True)),
            ('last_name', self.gf('django.db.models.fields.CharField')(max_length=150, null=True)),
            ('headline', self.gf('django.db.models.fields.TextField')(null=True)),
            ('status', self.gf('django.db.models.fields.CharField')(default='active', max_length=15)),
        ))
        db.send_create_signal('accounts', ['Profile'])

        # Adding model 'Picture'
        db.create_table('accounts_picture', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('person', self.gf('django.db.models.fields.related.ForeignKey')(related_name='pictures', to=orm['accounts.Profile'])),
            ('pic', self.gf('django.db.models.fields.files.ImageField')(max_length=450)),
            ('source', self.gf('django.db.models.fields.CharField')(max_length=45, null=True)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True)),
            ('license', self.gf('django.db.models.fields.TextField')(null=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('status', self.gf('django.db.models.fields.CharField')(default='active', max_length=15)),
        ))
        db.send_create_signal('accounts', ['Picture'])

        # Adding model 'Connection'
        db.create_table('accounts_connection', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('person1', self.gf('django.db.models.fields.related.ForeignKey')(related_name='person1', to=orm['accounts.Profile'])),
            ('person2', self.gf('django.db.models.fields.related.ForeignKey')(related_name='person2', to=orm['accounts.Profile'])),
            ('linked_on', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True)),
            ('service', self.gf('django.db.models.fields.CharField')(max_length=45)),
            ('status', self.gf('django.db.models.fields.CharField')(default='active', max_length=15)),
        ))
        db.send_create_signal('accounts', ['Connection'])


    def backwards(self, orm):
        # Deleting model 'Account'
        db.delete_table('accounts_account')

        # Deleting model 'Profile'
        db.delete_table('accounts_profile')

        # Deleting model 'Picture'
        db.delete_table('accounts_picture')

        # Deleting model 'Connection'
        db.delete_table('accounts_connection')


    models = {
        'accounts.account': {
            'Meta': {'object_name': 'Account'},
            'access_token': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True'}),
            'address': ('django.db.models.fields.CharField', [], {'max_length': '450', 'null': 'True'}),
            'expires_on': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_scanned': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'linked_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'account'", 'to': "orm['auth.User']"}),
            'public_url': ('django.db.models.fields.URLField', [], {'max_length': '450', 'null': 'True'}),
            'scanning_now': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'service': ('django.db.models.fields.CharField', [], {'max_length': '45'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'active'", 'max_length': '15'}),
            'token_secret': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True'}),
            'uniq_id': ('django.db.models.fields.CharField', [], {'max_length': '150', 'null': 'True'})
        },
        'accounts.connection': {
            'Meta': {'object_name': 'Connection'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'linked_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'person1': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'person1'", 'to': "orm['accounts.Profile']"}),
            'person2': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'person2'", 'to': "orm['accounts.Profile']"}),
            'service': ('django.db.models.fields.CharField', [], {'max_length': '45'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'active'", 'max_length': '15'})
        },
        'accounts.picture': {
            'Meta': {'object_name': 'Picture'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'license': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'pictures'", 'to': "orm['accounts.Profile']"}),
            'pic': ('django.db.models.fields.files.ImageField', [], {'max_length': '450'}),
            'source': ('django.db.models.fields.CharField', [], {'max_length': '45', 'null': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'active'", 'max_length': '15'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'accounts.profile': {
            'Meta': {'object_name': 'Profile'},
            'connections': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'connections+'", 'symmetrical': 'False', 'through': "orm['accounts.Connection']", 'to': "orm['accounts.Profile']"}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '150', 'null': 'True'}),
            'headline': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '150', 'null': 'True'}),
            'middle_name': ('django.db.models.fields.CharField', [], {'max_length': '150', 'null': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'active'", 'max_length': '15'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True'})
        },
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['accounts']