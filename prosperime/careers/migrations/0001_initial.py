# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Position'
        db.create_table('careers_position', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('entity', self.gf('django.db.models.fields.related.ForeignKey')(related_name='positions', to=orm['entities.Entity'])),
            ('person', self.gf('django.db.models.fields.related.ForeignKey')(related_name='positions', to=orm['auth.User'])),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=150, null=True)),
            ('summary', self.gf('django.db.models.fields.CharField')(max_length=450, null=True)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True)),
            ('current', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('start_date', self.gf('django.db.models.fields.DateField')(null=True)),
            ('end_date', self.gf('django.db.models.fields.DateField')(null=True)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=450, null=True)),
            ('degree', self.gf('django.db.models.fields.CharField')(max_length=450, null=True)),
            ('field', self.gf('django.db.models.fields.CharField')(max_length=450, null=True)),
            ('status', self.gf('django.db.models.fields.CharField')(default='active', max_length=15)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True)),
        ))
        db.send_create_signal('careers', ['Position'])

        # Adding M2M table for field careers on 'Position'
        db.create_table('careers_position_careers', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('position', models.ForeignKey(orm['careers.position'], null=False)),
            ('career', models.ForeignKey(orm['careers.career'], null=False))
        ))
        db.create_unique('careers_position_careers', ['position_id', 'career_id'])

        # Adding model 'Career'
        db.create_table('careers_career', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('short_name', self.gf('django.db.models.fields.CharField')(max_length=450, null=True)),
            ('long_name', self.gf('django.db.models.fields.CharField')(max_length=450, null=True)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(related_name='children', null=True, to=orm['careers.Career'])),
            ('census_code', self.gf('django.db.models.fields.CharField')(max_length=10, null=True)),
            ('soc_code', self.gf('django.db.models.fields.CharField')(max_length=15, null=True)),
            ('industry_code', self.gf('django.db.models.fields.CharField')(max_length=15, null=True)),
            ('pos_titles', self.gf('django.db.models.fields.TextField')(null=True)),
            ('status', self.gf('django.db.models.fields.CharField')(default='active', max_length=15)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True)),
        ))
        db.send_create_signal('careers', ['Career'])

        # Adding M2M table for field industry on 'Career'
        db.create_table('careers_career_industry', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('career', models.ForeignKey(orm['careers.career'], null=False)),
            ('industry', models.ForeignKey(orm['entities.industry'], null=False))
        ))
        db.create_unique('careers_career_industry', ['career_id', 'industry_id'])

        # Adding model 'SavedCareer'
        db.create_table('careers_savedcareer', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('career', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['careers.Career'])),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=150, null=True)),
            ('status', self.gf('django.db.models.fields.CharField')(default='active', max_length=15)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True)),
        ))
        db.send_create_signal('careers', ['SavedCareer'])

        # Adding model 'IdealPosition'
        db.create_table('careers_idealposition', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=450)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True)),
            ('status', self.gf('django.db.models.fields.CharField')(default='active', max_length=15)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True)),
        ))
        db.send_create_signal('careers', ['IdealPosition'])

        # Adding M2M table for field careers on 'IdealPosition'
        db.create_table('careers_idealposition_careers', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('idealposition', models.ForeignKey(orm['careers.idealposition'], null=False)),
            ('career', models.ForeignKey(orm['careers.career'], null=False))
        ))
        db.create_unique('careers_idealposition_careers', ['idealposition_id', 'career_id'])

        # Adding model 'GoalPosition'
        db.create_table('careers_goalposition', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('position', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['careers.IdealPosition'])),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('status', self.gf('django.db.models.fields.CharField')(default='active', max_length=15)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True)),
        ))
        db.send_create_signal('careers', ['GoalPosition'])

        # Adding model 'SavedPath'
        db.create_table('careers_savedpath', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=50, null=True)),
            ('date_created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True)),
            ('date_modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True)),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(related_name='savedpath', to=orm['auth.User'])),
            ('last_index', self.gf('django.db.models.fields.CharField')(max_length=10, null=True)),
        ))
        db.send_create_signal('careers', ['SavedPath'])

        # Adding model 'SavedPosition'
        db.create_table('careers_savedposition', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('position', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['careers.Position'])),
            ('path', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['careers.SavedPath'])),
            ('index', self.gf('django.db.models.fields.CharField')(max_length=10, null=True)),
        ))
        db.send_create_signal('careers', ['SavedPosition'])


    def backwards(self, orm):
        # Deleting model 'Position'
        db.delete_table('careers_position')

        # Removing M2M table for field careers on 'Position'
        db.delete_table('careers_position_careers')

        # Deleting model 'Career'
        db.delete_table('careers_career')

        # Removing M2M table for field industry on 'Career'
        db.delete_table('careers_career_industry')

        # Deleting model 'SavedCareer'
        db.delete_table('careers_savedcareer')

        # Deleting model 'IdealPosition'
        db.delete_table('careers_idealposition')

        # Removing M2M table for field careers on 'IdealPosition'
        db.delete_table('careers_idealposition_careers')

        # Deleting model 'GoalPosition'
        db.delete_table('careers_goalposition')

        # Deleting model 'SavedPath'
        db.delete_table('careers_savedpath')

        # Deleting model 'SavedPosition'
        db.delete_table('careers_savedposition')


    models = {
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
        'careers.career': {
            'Meta': {'object_name': 'Career'},
            'census_code': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'industry': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['entities.Industry']", 'symmetrical': 'False'}),
            'industry_code': ('django.db.models.fields.CharField', [], {'max_length': '15', 'null': 'True'}),
            'long_name': ('django.db.models.fields.CharField', [], {'max_length': '450', 'null': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'children'", 'null': 'True', 'to': "orm['careers.Career']"}),
            'pos_titles': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'saved_people': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'saved_careers'", 'symmetrical': 'False', 'through': "orm['careers.SavedCareer']", 'to': "orm['auth.User']"}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '450', 'null': 'True'}),
            'soc_code': ('django.db.models.fields.CharField', [], {'max_length': '15', 'null': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'active'", 'max_length': '15'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'})
        },
        'careers.goalposition': {
            'Meta': {'object_name': 'GoalPosition'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'position': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['careers.IdealPosition']"}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'active'", 'max_length': '15'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'})
        },
        'careers.idealposition': {
            'Meta': {'object_name': 'IdealPosition'},
            'careers': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'ideal_positions'", 'symmetrical': 'False', 'to': "orm['careers.Career']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'people': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.User']", 'through': "orm['careers.GoalPosition']", 'symmetrical': 'False'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'active'", 'max_length': '15'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '450'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'})
        },
        'careers.position': {
            'Meta': {'object_name': 'Position'},
            'careers': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'positions'", 'symmetrical': 'False', 'to': "orm['careers.Career']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'current': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'degree': ('django.db.models.fields.CharField', [], {'max_length': '450', 'null': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'end_date': ('django.db.models.fields.DateField', [], {'null': 'True'}),
            'entity': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'positions'", 'to': "orm['entities.Entity']"}),
            'field': ('django.db.models.fields.CharField', [], {'max_length': '450', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'positions'", 'to': "orm['auth.User']"}),
            'start_date': ('django.db.models.fields.DateField', [], {'null': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'active'", 'max_length': '15'}),
            'summary': ('django.db.models.fields.CharField', [], {'max_length': '450', 'null': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '150', 'null': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '450', 'null': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'})
        },
        'careers.savedcareer': {
            'Meta': {'object_name': 'SavedCareer'},
            'career': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['careers.Career']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'active'", 'max_length': '15'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '150', 'null': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'})
        },
        'careers.savedpath': {
            'Meta': {'object_name': 'SavedPath'},
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'date_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_index': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'savedpath'", 'to': "orm['auth.User']"}),
            'positions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['careers.Position']", 'through': "orm['careers.SavedPosition']", 'symmetrical': 'False'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True'})
        },
        'careers.savedposition': {
            'Meta': {'ordering': "['-index']", 'object_name': 'SavedPosition'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'index': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True'}),
            'path': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['careers.SavedPath']"}),
            'position': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['careers.Position']"})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'entities.entity': {
            'Meta': {'object_name': 'Entity'},
            'aliases': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'blog_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'cb_permalink': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True', 'blank': 'True'}),
            'cb_type': ('django.db.models.fields.CharField', [], {'max_length': '25', 'null': 'True', 'blank': 'True'}),
            'cb_updated': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'cb_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'deadpooled_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'domains': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['entities.Industry']", 'symmetrical': 'False'}),
            'founded_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'li_last_scanned': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'li_type': ('django.db.models.fields.CharField', [], {'max_length': '15', 'null': 'True'}),
            'li_uniq_id': ('django.db.models.fields.CharField', [], {'max_length': '150', 'null': 'True'}),
            'li_univ_name': ('django.db.models.fields.CharField', [], {'max_length': '450', 'null': 'True'}),
            'li_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '450'}),
            'no_employees': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'size_range': ('django.db.models.fields.CharField', [], {'max_length': '45', 'null': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'active'", 'max_length': '15'}),
            'subtype': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'summary': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'total_money': ('django.db.models.fields.CharField', [], {'max_length': '15', 'null': 'True', 'blank': 'True'}),
            'twitter_handle': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '25'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'web_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'})
        },
        'entities.industry': {
            'Meta': {'object_name': 'Industry'},
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'li_code': ('django.db.models.fields.CharField', [], {'max_length': '5', 'null': 'True'}),
            'li_group': ('django.db.models.fields.CharField', [], {'max_length': '15', 'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '150'})
        }
    }

    complete_apps = ['careers']